"""Auth tests: open-mode behaviour, the token primitives, and enabled-mode enforcement.

The shared ``client`` fixture (conftest) runs with auth OPEN by default, so the
config/login/me happy paths exercise the open path. Enabled-mode is verified by
monkeypatching ``app.api.deps.get_settings`` to return a copy of Settings with
``auth_enabled=True`` -- no env/process mutation, and monkeypatch auto-restores.
"""
from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.security import create_token, verify_credentials, verify_token


def test_auth_config_open(client) -> None:
    resp = client.get("/api/auth/config")
    assert resp.status_code == 200
    assert resp.json() == {"authEnabled": False}


def test_login_open_issues_token(client) -> None:
    resp = client.post("/api/auth/login", json={"username": "admin", "password": ""})
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "admin"
    assert isinstance(body["token"], str)
    assert body["token"]  # non-empty


def test_me_with_bearer_token(client) -> None:
    login = client.post("/api/auth/login", json={"username": "admin", "password": ""})
    token = login.json()["token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == {"username": "admin"}


def test_me_open_no_header_returns_admin(client) -> None:
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json() == {"username": "admin"}


def test_token_roundtrip_and_credentials() -> None:
    assert verify_token(create_token("x")) == "x"
    assert verify_token("garbage") is None
    assert verify_credentials("admin", "omnivra") is True
    assert verify_credentials("admin", "wrong") is False
    assert verify_credentials("nope", "omnivra") is False


def test_enabled_mode_enforced(client, monkeypatch) -> None:
    """With auth enabled, /me needs a valid Bearer token (401 without, 200 with)."""
    base = get_settings()
    enabled = Settings(**{**base.model_dump(), "auth_enabled": True})
    # require_user resolves settings via the get_settings symbol imported into deps.
    monkeypatch.setattr("app.api.deps.get_settings", lambda: enabled)

    no_header = client.get("/api/auth/me")
    assert no_header.status_code == 401

    # create_token signs with security.get_settings().api_secret_key, which is
    # unchanged (we only flipped auth_enabled in the deps copy), so it verifies.
    token = create_token("admin")
    with_token = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert with_token.status_code == 200
    assert with_token.json() == {"username": "admin"}
