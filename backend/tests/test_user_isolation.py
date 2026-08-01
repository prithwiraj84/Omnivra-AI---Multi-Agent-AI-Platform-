"""Per-user private workspaces (cp-0067): a verified Supabase JWT scopes every project.

Open mode (no SUPABASE_JWT_SECRET, the default) is unchanged — one admin owns everything, no
auth required. Turning the secret on (the `multiuser` fixture) makes the backend verify each
request's Supabase access token and isolate projects/tasks/dashboard per user id (`sub`).
"""
from __future__ import annotations

import time

import jwt
import pytest

from app.core.config import get_settings

_SECRET = "test-supabase-jwt-secret-0123456789"


def _token(sub: str, *, secret: str = _SECRET, aud: str = "authenticated", exp_offset: int = 3600) -> str:
    payload = {"sub": sub, "aud": aud, "role": "authenticated", "exp": int(time.time()) + exp_offset}
    return jwt.encode(payload, secret, algorithm="HS256")


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def multiuser(monkeypatch):
    """Enable per-user isolation for a test by giving the cached settings a JWT secret."""
    monkeypatch.setattr(get_settings(), "supabase_jwt_secret", _SECRET, raising=False)
    yield


@pytest.fixture
def es256(monkeypatch):
    """Per-user mode for a project on the MODERN asymmetric signing keys (ES256 + JWKS).

    Generates a throwaway P-256 key, serves it as a JWKS, and patches the JWKS client so no
    network call happens. Mirrors a real Supabase project that has migrated off the legacy
    shared secret (its /auth/v1/.well-known/jwks.json publishes an ES256 key).
    """
    from cryptography.hazmat.primitives.asymmetric import ec

    from app.api import deps

    priv = ec.generate_private_key(ec.SECP256R1())

    # Per-user mode ON via the explicit switch; no HS256 secret exists for such a project.
    monkeypatch.setattr(get_settings(), "per_user_workspaces", True, raising=False)
    monkeypatch.setattr(get_settings(), "supabase_jwt_secret", None, raising=False)
    monkeypatch.setattr(get_settings(), "supabase_url", "https://proj.supabase.co", raising=False)

    class _Key:
        key = priv.public_key()

    class _Client:
        def __init__(self, *a, **k) -> None: ...
        def get_signing_key_from_jwt(self, _token):  # noqa: ANN001
            return _Key()

    deps._jwks_client.cache_clear()
    monkeypatch.setattr(deps.jwt, "PyJWKClient", _Client)

    def issue(sub: str, *, exp_offset: int = 3600) -> str:
        return jwt.encode(
            {"sub": sub, "aud": "authenticated", "exp": int(time.time()) + exp_offset},
            priv,
            algorithm="ES256",
        )

    yield issue
    deps._jwks_client.cache_clear()


# --- open mode (default) is unchanged --------------------------------------
def test_open_mode_needs_no_auth_and_sees_seeds(client):
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    assert any(p["id"] == "proj-dashboard" for p in resp.json())  # seeds visible to the admin


# --- per-user mode requires a valid Supabase token -------------------------
def test_multiuser_requires_valid_token(client, multiuser):
    assert client.get("/api/projects").status_code == 401  # no token
    assert client.get("/api/projects", headers=_auth("not-a-jwt")).status_code == 401  # malformed
    assert client.get("/api/projects", headers=_auth(_token("u", secret="wrong"))).status_code == 401  # bad signature
    assert client.get("/api/projects", headers=_auth(_token("u", exp_offset=-10))).status_code == 401  # expired


# --- projects are private per user -----------------------------------------
def test_projects_isolated_between_users(client, multiuser):
    a, b = _token("user-A"), _token("user-B")

    # new users start EMPTY (the admin-owned seeds are hidden)
    assert client.get("/api/projects", headers=_auth(a)).json() == []

    created = client.post("/api/projects", json={"name": "A's private plan"}, headers=_auth(a))
    assert created.status_code == 200
    pid = created.json()["id"]

    # A sees it; B never does
    assert any(p["id"] == pid for p in client.get("/api/projects", headers=_auth(a)).json())
    assert all(p["id"] != pid for p in client.get("/api/projects", headers=_auth(b)).json())

    # B can't open or delete A's project — 404 (not 403), so existence isn't revealed
    assert client.get(f"/api/projects/{pid}", headers=_auth(b)).status_code == 404
    assert client.delete(f"/api/projects/{pid}", headers=_auth(b)).status_code == 404

    # A can, and cleans up
    assert client.get(f"/api/projects/{pid}", headers=_auth(a)).status_code == 200
    assert client.delete(f"/api/projects/{pid}", headers=_auth(a)).status_code == 200


# --- dashboard + tasks are gated and scoped --------------------------------
def test_dashboard_and_tasks_scoped(client, multiuser):
    a = _token("user-C")
    assert client.get("/api/dashboard").status_code == 401  # gated
    assert client.get("/api/dashboard", headers=_auth(a)).status_code == 200  # own scope, no crash
    assert client.get("/api/tasks").status_code == 401
    assert client.get("/api/tasks", headers=_auth(a)).json() == []  # no tasks in an empty private space


# --- a foreign project id can't be addressed via X-Project-Id --------------
def test_es256_project_tokens_are_accepted(client, es256):
    """Regression for the production 401: a project on the modern asymmetric signing keys issues
    ES256 tokens, which must verify via JWKS (they can't be checked with the legacy HS256 secret)."""
    a, b = es256("es-user-A"), es256("es-user-B")

    # the dashboard — the endpoint that was returning 401 in production — now works
    assert client.get("/api/dashboard", headers=_auth(a)).status_code == 200
    # ...and still rejects the unauthenticated + expired cases
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/dashboard", headers=_auth(es256("x", exp_offset=-30))).status_code == 401

    # isolation still holds across two ES256 users
    assert client.get("/api/projects", headers=_auth(a)).json() == []
    pid = client.post("/api/projects", json={"name": "ES private"}, headers=_auth(a)).json()["id"]
    try:
        assert all(p["id"] != pid for p in client.get("/api/projects", headers=_auth(b)).json())
        assert client.get(f"/api/projects/{pid}", headers=_auth(b)).status_code == 404
    finally:
        client.delete(f"/api/projects/{pid}", headers=_auth(a))


def test_foreign_project_id_rejected(client, multiuser):
    a, b = _token("user-D"), _token("user-E")
    pid = client.post("/api/projects", json={"name": "D data"}, headers=_auth(a)).json()["id"]
    try:
        # B tries to reach A's project through the project-scoped workspace API
        r = client.get("/api/workspace/artifacts", headers={**_auth(b), "X-Project-Id": pid})
        assert r.status_code == 404
    finally:
        client.delete(f"/api/projects/{pid}", headers=_auth(a))
