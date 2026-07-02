"""In-app provider API-key config (cp-0060): SecretsStore, resolver, masking, endpoints.

The suite neutralizes all provider env vars (conftest), so providers are unconfigured by
default. Each test cleans up any stored key it writes so the process-wide SecretsStore +
provider registry singletons stay pristine for other test modules.
"""
from __future__ import annotations

import asyncio

import pytest

from app.core.config import get_settings
from app.providers.base import BaseProvider, CompletionRequest, CompletionResponse, RateLimitError
from app.providers.registry import get_provider_registry
from app.services.provider_keys import (
    PROVIDER_KEY_CATALOG,
    SOCIAL_CONNECTORS,
    connector_configured,
    is_known_provider,
    key_source,
    mask_key,
    provider_key_status,
    resolve_provider_key,
    social_connector_status,
)
from app.services.secrets_store import get_secrets_store

_ALL_KEYS = [s.id for s in PROVIDER_KEY_CATALOG] + [f.key for c in SOCIAL_CONNECTORS for f in c.fields]


@pytest.fixture(autouse=True)
def _clean_store():
    """Clear every catalog + connector-field key before and after each test (shared singleton)."""
    store = get_secrets_store()
    for k in _ALL_KEYS:
        store.clear(k)
    yield
    for k in _ALL_KEYS:
        store.clear(k)


# --- masking ---------------------------------------------------------------
def test_mask_key_none_and_short():
    assert mask_key(None) is None
    assert mask_key("") is None
    assert mask_key("abc") == "•••"  # <= 8 fully bulleted
    assert mask_key("12345678") == "•" * 8


def test_mask_key_long_shows_only_prefix_and_last4():
    masked = mask_key("sk-or-v1-abcdef0123456789wxyz")
    assert masked == "sk-o…wxyz"
    # never leaks more than 8 real chars
    assert "abcdef" not in masked


# --- SecretsStore ----------------------------------------------------------
def test_store_set_get_clear_and_epoch():
    store = get_secrets_store()
    start = store.epoch
    assert store.get("openrouter") is None
    store.set("openrouter", "sk-or-test-123")
    assert store.get("openrouter") == "sk-or-test-123"
    assert store.epoch == start + 1
    assert "openrouter" in store.stored_providers()
    assert store.clear("openrouter") is True
    assert store.get("openrouter") is None
    assert store.epoch == start + 2
    assert store.clear("openrouter") is False  # already gone -> no epoch bump
    assert store.epoch == start + 2


def test_store_rejects_bad_values():
    store = get_secrets_store()
    with pytest.raises(ValueError):
        store.set("groq", "   ")  # empty after strip
    with pytest.raises(ValueError):
        store.set("groq", "key1,key2")  # comma would split into a bogus pool
    with pytest.raises(ValueError):
        store.set("groq", "key with space")
    assert store.get("groq") is None


def test_store_persists_to_disk_atomically():
    store = get_secrets_store()
    store.set("pexels", "pexels-abc")
    path = get_settings().workspace_path / ".state" / "provider_keys.json"
    assert path.exists()
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["keys"]["pexels"] == "pexels-abc"
    assert not path.with_suffix(".json.tmp").exists()  # temp cleaned up by os.replace


# --- resolver precedence ---------------------------------------------------
def test_resolve_precedence_stored_over_env(monkeypatch):
    store = get_secrets_store()
    # env empty (conftest) -> none
    assert resolve_provider_key("openrouter") is None
    assert key_source("openrouter") == "none"

    # env only -> env
    monkeypatch.setattr(get_settings(), "openrouter_api_key", "env-key-abc", raising=False)
    assert resolve_provider_key("openrouter") == "env-key-abc"
    assert key_source("openrouter") == "env"

    # stored overrides env
    store.set("openrouter", "stored-key-xyz")
    assert resolve_provider_key("openrouter") == "stored-key-xyz"
    assert key_source("openrouter") == "stored"

    # clear -> falls back to env
    store.clear("openrouter")
    assert resolve_provider_key("openrouter") == "env-key-abc"


def test_unknown_provider():
    assert is_known_provider("openrouter") is True
    assert is_known_provider("nope") is False
    assert resolve_provider_key("nope") is None


# --- status shape ----------------------------------------------------------
def test_provider_key_status_shape_no_raw_secrets():
    get_secrets_store().set("groq", "gsk-secret-value-1234")
    rows = {r["id"]: r for r in provider_key_status()}
    assert set(rows) == {s.id for s in PROVIDER_KEY_CATALOG}
    groq = rows["groq"]
    assert groq["storedSet"] is True
    assert groq["source"] == "stored"
    assert groq["configured"] is True
    assert groq["masked"] == "gsk-…1234"
    # the raw secret is never present anywhere in the payload
    assert "gsk-secret-value-1234" not in str(rows)
    # an unset provider reports cleanly
    assert rows["huggingface"]["configured"] is False
    assert rows["huggingface"]["masked"] is None


# --- registry in-place refresh --------------------------------------------
def test_registry_picks_up_saved_key_without_restart():
    reg = get_provider_registry()
    assert reg.get("openrouter").is_configured is False
    get_secrets_store().set("openrouter", "sk-or-live-key")
    # epoch advanced -> the cached client is refreshed in place on the next get()
    assert reg.get("openrouter").is_configured is True
    get_secrets_store().clear("openrouter")
    assert reg.get("openrouter").is_configured is False


# --- API endpoints ---------------------------------------------------------
def test_endpoints_get_set_clear(client):
    # GET list
    resp = client.get("/api/system/provider-keys")
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()}
    assert {"google_ai", "openrouter", "groq", "huggingface", "pexels"} <= ids

    # PUT set
    resp = client.put("/api/system/provider-keys/openrouter", json={"value": "sk-or-endpoint-123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "openrouter"
    assert body["source"] == "stored"
    assert body["configured"] is True
    assert body["masked"] == "sk-o…-123"
    assert "sk-or-endpoint-123" not in resp.text  # masked only

    # GET reflects it
    row = next(r for r in client.get("/api/system/provider-keys").json() if r["id"] == "openrouter")
    assert row["storedSet"] is True

    # DELETE clears it
    resp = client.delete("/api/system/provider-keys/openrouter")
    assert resp.status_code == 200
    assert resp.json()["storedSet"] is False


def test_endpoint_unknown_provider_404(client):
    assert client.put("/api/system/provider-keys/bogus", json={"value": "x"}).status_code == 404
    assert client.delete("/api/system/provider-keys/bogus").status_code == 404


def test_endpoint_invalid_value_422(client):
    assert client.put("/api/system/provider-keys/groq", json={"value": "a,b"}).status_code == 422
    assert client.put("/api/system/provider-keys/groq", json={"value": ""}).status_code == 422


# --- concurrency: a key change mid-call must not IndexError (cp-0060 review fix) -------------
class _DummyProvider(BaseProvider):
    name = "dummy"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:  # pragma: no cover
        raise NotImplementedError


def test_acall_survives_concurrent_pool_shrink():
    """set_keys() shrinking the pool DURING an _acall must not raise IndexError — the call
    iterates a stable snapshot of keys, not live indices."""
    provider = _DummyProvider(api_key="k1,k2,k3")
    seen: list[str] = []

    async def run(key: str) -> str:
        seen.append(key)
        if len(seen) == 1:
            provider.set_keys("only")  # concurrent refresh shrinks the pool to 1
            raise RateLimitError("429")
        return "ok"

    assert asyncio.run(provider._acall(run)) == "ok"
    assert len(seen) == 2  # rotated to the 2nd key of the ORIGINAL 3-key snapshot, no IndexError


# --- social publishing connectors (cp-0063 Phase A) ----------------------------------------
def test_social_connector_status_shape_no_raw_secrets():
    rows = {r["id"]: r for r in social_connector_status()}
    assert {"youtube", "linkedin", "facebook", "instagram", "twitter"} <= set(rows)
    # nothing configured out of the box (conftest neutralizes env)
    assert rows["twitter"]["configured"] is False
    assert rows["twitter"]["publishSupported"] is True
    assert rows["youtube"]["publishSupported"] is True
    assert rows["instagram"]["publishSupported"] is True
    # X (Twitter) exposes the OAuth1 quad, all secret + required
    tw_fields = {f["key"] for f in rows["twitter"]["fields"]}
    assert tw_fields == {"twitter_api_key", "twitter_api_secret", "twitter_access_token", "twitter_access_secret"}
    for f in rows["twitter"]["fields"]:
        assert f["masked"] is None and f["storedSet"] is False


def test_connector_configured_requires_all_required_fields():
    store = get_secrets_store()
    assert connector_configured("linkedin") is False
    store.set("linkedin_access_token", "li-token-abcdef")
    assert connector_configured("linkedin") is True

    # twitter needs all four; one missing -> not configured
    assert connector_configured("twitter") is False
    store.set("twitter_api_key", "ak")
    store.set("twitter_api_secret", "as")
    store.set("twitter_access_token", "at")
    assert connector_configured("twitter") is False
    store.set("twitter_access_secret", "asec")
    assert connector_configured("twitter") is True


def test_social_field_resolver_precedence(monkeypatch):
    # env fallback for a social field
    assert resolve_provider_key("facebook_page_token") is None
    monkeypatch.setattr(get_settings(), "facebook_page_token", "env-fb-tok", raising=False)
    assert resolve_provider_key("facebook_page_token") == "env-fb-tok"
    # stored overrides env
    get_secrets_store().set("facebook_page_token", "stored-fb-tok")
    assert resolve_provider_key("facebook_page_token") == "stored-fb-tok"


def test_publishers_is_configured_reflects_stored_creds():
    from app.services import publishers

    assert publishers.is_configured("facebook") is False
    get_secrets_store().set("facebook_page_id", "123")
    get_secrets_store().set("facebook_page_token", "fb-token")
    assert publishers.is_configured("facebook") is True


def test_social_connector_endpoints(client):
    # GET
    resp = client.get("/api/system/social-connectors")
    assert resp.status_code == 200
    ids = {c["id"] for c in resp.json()}
    assert {"youtube", "linkedin", "facebook", "instagram", "twitter"} <= ids

    # PUT multiple fields at once
    resp = client.put(
        "/api/system/social-connectors/facebook",
        json={"values": {"facebook_page_id": "998877", "facebook_page_token": "EAAG-secret-token"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    fields = {f["key"]: f for f in body["fields"]}
    assert fields["facebook_page_token"]["masked"] == "EAAG…oken"
    assert "EAAG-secret-token" not in resp.text  # masked only

    # stray field key for another connector is ignored
    resp = client.put("/api/system/social-connectors/linkedin", json={"values": {"facebook_page_id": "x", "linkedin_access_token": "li-tok"}})
    assert resp.status_code == 200
    assert resp.json()["configured"] is True
    # the facebook field was NOT overwritten by the linkedin PUT
    fb = next(c for c in client.get("/api/system/social-connectors").json() if c["id"] == "facebook")
    assert {f["key"]: f["masked"] for f in fb["fields"]}["facebook_page_id"] is not None

    # clearing a required field (empty value) drops "configured"
    resp = client.put("/api/system/social-connectors/facebook", json={"values": {"facebook_page_token": ""}})
    assert resp.json()["configured"] is False

    # DELETE clears the whole connector
    resp = client.delete("/api/system/social-connectors/linkedin")
    assert resp.status_code == 200
    assert resp.json()["configured"] is False

    assert client.put("/api/system/social-connectors/bogus", json={"values": {}}).status_code == 404
    assert client.delete("/api/system/social-connectors/bogus").status_code == 404
