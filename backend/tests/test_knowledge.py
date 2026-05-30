"""Knowledge Base API tests (Phase 9 RAG): add docs, semantic search, stats, and
workspace ingestion after a workflow run.

Reuses the session-scoped ``client`` fixture from :mod:`tests.conftest`. The store
is camelCase on the wire (``SearchResult``: id/text/score/metadata). Ingestion is
exercised after a real ``POST /api/workflows/run`` so there are workspace artifacts
to index (the orchestrator persists every agent output to the temp workspace).
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_add_document_returns_id(client: TestClient) -> None:
    resp = client.post(
        "/api/knowledge",
        json={
            "text": "Omnivra uses LangGraph for CEO to department orchestration",
            "source": "note",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"], "add must return a non-empty id"


def test_search_and_stats_after_adding_docs(client: TestClient) -> None:
    first = client.post(
        "/api/knowledge",
        json={
            "text": "Omnivra uses LangGraph for CEO to department orchestration",
            "source": "note",
        },
    )
    assert first.status_code == 200
    assert first.json()["id"]

    second = client.post(
        "/api/knowledge",
        json={
            "text": "The dashboard frontend is built with React Query and a glass UI kit",
            "source": "note",
        },
    )
    assert second.status_code == 200
    assert second.json()["id"]

    search = client.get("/api/knowledge/search", params={"q": "orchestration graph", "k": 2})
    assert search.status_code == 200
    results = search.json()
    assert results, "search must return at least one hit"
    top = results[0]
    assert "orchestration" in top["text"].lower()
    assert top["score"] > 0
    assert "id" in top and "metadata" in top

    stats = client.get("/api/knowledge/stats")
    assert stats.status_code == 200
    assert stats.json()["count"] >= 2


def test_ingest_workspace_after_run_indexes_artifacts(client: TestClient) -> None:
    run = client.post("/api/workflows/run", json={"task": "Write the Omnivra product brief"})
    assert run.status_code == 200
    assert run.json()["agentOutputs"], "run must produce agent outputs (workspace artifacts)"

    ingest = client.post("/api/knowledge/ingest-workspace")
    assert ingest.status_code == 200
    body = ingest.json()
    assert body["ingested"] >= 1
    assert body["total"] >= body["ingested"]
