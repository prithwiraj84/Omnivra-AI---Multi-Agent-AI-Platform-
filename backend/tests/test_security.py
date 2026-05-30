"""Hardening test: security response headers are present (security_headers_enabled defaults True)."""
from __future__ import annotations


def test_security_headers_present(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    # Header lookups are case-insensitive in Starlette's Headers mapping.
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
