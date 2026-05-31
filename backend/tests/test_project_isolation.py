"""Per-project workspace isolation + cascade hard-delete (cp-0015).

Each project owns an isolated subtree under workspace/projects/<project_id>/:
artifacts, RAG memory, and workflow run records never bleed across projects. The
active project is selected with the ``X-Project-Id`` header and must exist in the
catalog (unknown/deleted ids are rejected, so a stale id can't recreate a purged
subtree). Deleting a project hard-deletes its entire subtree. Runs are offline.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.workspace_fs.paths import project_root


def _new_project(client: TestClient, name: str) -> str:
    """Create a project via the API and return its id (project must exist to be used)."""
    res = client.post("/api/projects", json={"name": name})
    assert res.status_code == 200
    return res.json()["id"]


def _hdr(pid: str) -> dict[str, str]:
    return {"X-Project-Id": pid}


def _count(client: TestClient, pid: str, path: str) -> int:
    res = client.get(path, headers=_hdr(pid))
    assert res.status_code == 200
    return res.json()["count"]


def test_memory_is_isolated_per_project(client: TestClient) -> None:
    a = _new_project(client, "Isolation A")
    b = _new_project(client, "Isolation B")

    # Fresh projects start with empty memory stores.
    a0 = _count(client, a, "/api/memory/stats")
    b0 = _count(client, b, "/api/memory/stats")

    # A run scoped to project A only grows A's memory.
    run_a = client.post("/api/workflows/run", json={"task": "Alpha widget engine spec"}, headers=_hdr(a))
    assert run_a.status_code == 200
    assert run_a.json()["projectId"] == a

    assert _count(client, a, "/api/memory/stats") > a0, "A's memory must grow"
    assert _count(client, b, "/api/memory/stats") == b0, "B's memory must NOT change (isolation)"

    # A run scoped to project B only grows B's memory.
    a1 = _count(client, a, "/api/memory/stats")
    run_b = client.post("/api/workflows/run", json={"task": "Beta sprocket factory"}, headers=_hdr(b))
    assert run_b.status_code == 200
    assert _count(client, b, "/api/memory/stats") > b0, "B's memory must grow"
    assert _count(client, a, "/api/memory/stats") == a1, "A's memory must NOT change (isolation)"


def test_artifacts_are_isolated_per_project(client: TestClient) -> None:
    a = _new_project(client, "Artifacts A")
    fresh = _new_project(client, "Artifacts Fresh")

    client.post("/api/workflows/run", json={"task": "Write the gamma onboarding doc"}, headers=_hdr(a))

    listing_a = client.get("/api/workspace/artifacts", headers=_hdr(a))
    assert listing_a.status_code == 200
    assert listing_a.json(), "A must have artifacts after a run"

    # A brand-new project sees an empty workspace — no cross-project leakage.
    listing_fresh = client.get("/api/workspace/artifacts", headers=_hdr(fresh))
    assert listing_fresh.status_code == 200
    assert listing_fresh.json() == [], "a fresh project must see no other project's artifacts"


def test_workflow_runs_are_isolated_and_run_carries_project(client: TestClient) -> None:
    a = _new_project(client, "Runs A")
    none = _new_project(client, "Runs None")

    client.post("/api/workflows/run", json={"task": "Delta pipeline"}, headers=_hdr(a))
    runs_a = client.get("/api/workflows/runs", headers=_hdr(a)).json()
    runs_none = client.get("/api/workflows/runs", headers=_hdr(none)).json()
    assert runs_a, "A must list its own runs"
    assert all(r["projectId"] == a for r in runs_a)
    assert runs_none == [], "an unused project lists no runs"


def test_delete_project_cascades_hard_delete(client: TestClient) -> None:
    pid = _new_project(client, "Disposable")
    hdr = _hdr(pid)

    # Run a workflow so the project gets a real workspace subtree on disk.
    assert client.post("/api/workflows/run", json={"task": "throwaway"}, headers=hdr).status_code == 200
    assert project_root(pid).exists(), "the run must create the project's workspace dir"
    assert client.get("/api/workflows/runs", headers=hdr).json(), "the run must be recorded"

    # Delete -> hard-delete the whole subtree.
    deleted = client.delete(f"/api/projects/{pid}")
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}
    assert not project_root(pid).exists(), "delete must remove the project's workspace subtree"
    assert client.get(f"/api/projects/{pid}").status_code == 404


def test_default_workspace_cannot_be_deleted(client: TestClient) -> None:
    res = client.delete("/api/projects/__default__")
    assert res.status_code == 400


def test_invalid_project_id_is_rejected(client: TestClient) -> None:
    # A traversal attempt in the header is a 400 (per-project path jail).
    res = client.get("/api/memory/stats", headers={"X-Project-Id": "../escape"})
    assert res.status_code == 400


def test_unknown_project_is_404(client: TestClient) -> None:
    # A syntactically-valid but non-existent project is a 404 (no skeleton recreation).
    res = client.get("/api/memory/stats", headers={"X-Project-Id": "proj-never-created-xyz"})
    assert res.status_code == 404
