"""Smoke test: the FastAPI app boots and the health probe responds."""
from __future__ import annotations

from app.agents.registry import AGENT_REGISTRY


def test_health_ok(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"] == "Omnivra AI Company OS"
    # The header card reads the agent count straight from the registry.
    assert body["agents"] == len(AGENT_REGISTRY)


def test_openapi_served(client) -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"] == "Omnivra AI Company OS"
