"""Memory / RAG API tests (Phase 9): a workflow run stores every agent output as
recallable memory, which the next run can search — this is the RAG loop.

Reuses the session-scoped ``client`` fixture from :mod:`tests.conftest`. The
offline provider stubs echo the task prompt into each output, so a run on a
"dashboard UI" task produces memory text that a "dashboard UI" query retrieves
with a positive top score.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_run_then_memory_is_searchable(client: TestClient) -> None:
    run = client.post("/api/workflows/run", json={"task": "Design the Omnivra dashboard UI"})
    assert run.status_code == 200
    # Fire-and-poll: the POST returns 'running'; the background run persists the outputs + memory
    # (TestClient runs the BackgroundTask before the next request, so /memory below sees them).
    assert run.json()["workflowId"]

    stats = client.get("/api/memory/stats")
    assert stats.status_code == 200
    assert stats.json()["count"] >= 1

    search = client.get("/api/memory/search", params={"q": "dashboard UI", "k": 3})
    assert search.status_code == 200
    hits = search.json()
    assert hits, "memory search must recall the stored run output"
    assert hits[0]["score"] > 0
    assert {"id", "text", "score", "metadata"}.issubset(hits[0].keys())


def test_memory_recent_returns_list(client: TestClient) -> None:
    # Ensure there is at least one memory regardless of test ordering.
    client.post("/api/workflows/run", json={"task": "Design the Omnivra dashboard UI"})

    recent = client.get("/api/memory/recent", params={"n": 5})
    assert recent.status_code == 200
    items = recent.json()
    assert isinstance(items, list)
    assert items, "recent must list stored memories after a run"
    assert {"id", "text", "metadata"}.issubset(items[0].keys())
