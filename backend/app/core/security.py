"""Minimal signed-token auth (stdlib only — no extra dependency).

Issues a compact ``<payload>.<sig>`` token where payload is base64url JSON {sub, exp}
and sig is an HMAC-SHA256 of the payload keyed by ``settings.api_secret_key``. Good
enough for a single-admin command center; swap for a full OIDC/JWT provider in prod
if multi-user. Auth is opt-in (settings.auth_enabled).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from app.core.config import get_settings


def _b64u_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _sign(payload_b64: str, secret: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return _b64u_encode(sig)


def create_token(username: str, *, ttl_seconds: int | None = None) -> str:
    """Create a signed token for ``username``."""
    settings = get_settings()
    ttl = ttl_seconds if ttl_seconds is not None else settings.token_ttl_seconds
    payload = {"sub": username, "exp": int(time.time()) + ttl}
    payload_b64 = _b64u_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{payload_b64}.{_sign(payload_b64, settings.api_secret_key)}"


def verify_token(token: str) -> str | None:
    """Return the username if the token is valid + unexpired, else None."""
    try:
        payload_b64, sig = token.split(".", 1)
    except ValueError:
        return None
    expected = _sign(payload_b64, get_settings().api_secret_key)
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(_b64u_decode(payload_b64))
    except Exception:  # noqa: BLE001
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload.get("sub")


def verify_credentials(username: str, password: str) -> bool:
    """Constant-time check of the configured admin credentials."""
    settings = get_settings()
    u_ok = hmac.compare_digest(username or "", settings.admin_username)
    p_ok = hmac.compare_digest(password or "", settings.admin_password)
    return u_ok and p_ok
