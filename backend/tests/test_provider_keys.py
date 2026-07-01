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
    is_known_provider,
    key_source,
    mask_key,
    provider_key_status,
    resolve_provider_key,
)
from app.services.secrets_store import get_secrets_store


@pytest.fixture(autouse=True)
def _clean_store():
    """Clear every catalog key before and after each test (shared singleton store)."""
    store = get_secrets_store()
    for spec in PROVIDER_KEY_CATALOG:
        store.clear(spec.id)
    yield
    for spec in PROVIDER_KEY_CATALOG:
        store.clear(spec.id)


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
