"""Phase 7 tests: the Human Approval Gate run -> pause -> resume + recovery flow.

These exercise the live LangGraph interrupt/resume cycle end-to-end over HTTP.
Because the LangGraph checkpointer is the process-wide in-memory ``MemorySaver``,
the resume decision MUST be POSTed in the SAME process that started the run — so
every test here reuses the session-scoped ``client`` fixture from
:mod:`tests.conftest` (a single ``TestClient`` over ``app.main.app``).

Wire contract (camelCase RunResult):
    { workflowId, status, task, plan, delegations, agentOutputs[], recursionCount,
      result, errors[], pendingApproval: {approvalId, kind, summary, requestedBy} | null }

Gated tasks (publish/deploy/export/release/go live/presentation/final) pause:
    status == 'awaiting_approval', pendingApproval.approvalId startswith 'apr_'.
A decision resumes: approve/retry -> 'completed' (result.ok True),
reject -> 'failed', rollback -> 'rolled_back'. Unknown approvalId -> 404.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

GATED_TASK = "Publish and deploy the release"


def _start_gated_run(client: TestClient) -> dict:
    """POST a gated task and assert it paused at the approval gate; return the body."""
    resp = client.post("/api/workflows/run", json={"task": GATED_TASK})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "awaiting_approval", body
    pending = body["pendingApproval"]
    assert pending is not None
    assert pending["approvalId"].startswith("apr_"), pending
    assert body["agentOutputs"], "a paused run must already carry agent outputs"
    return body


# --------------------------------------------------------------------------- #
# Gate -> approve -> completed (outputs preserved, result.ok True).
# --------------------------------------------------------------------------- #
def test_run_gate_then_approve(client: TestClient) -> None:
    paused = _start_gated_run(client)
    approval_id = paused["pendingApproval"]["approvalId"]
    paused_output_count = len(paused["agentOutputs"])

    resp = client.post(f"/api/approvals/{approval_id}/decision", json={"action": "approve"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["status"] == "completed", body
    assert body["result"].get("ok") is True, body["result"]
    assert body["pendingApproval"] is None
    # The resumed run keeps (at least) the agent outputs produced before the pause.
    assert len(body["agentOutputs"]) >= paused_output_count
    assert body["workflowId"] == paused["workflowId"]


# --------------------------------------------------------------------------- #
# Gate -> reject -> failed (errors mention the rejection).
# --------------------------------------------------------------------------- #
def test_run_gate_then_reject(client: TestClient) -> None:
    paused = _start_gated_run(client)
    approval_id = paused["pendingApproval"]["approvalId"]

    resp = client.post(
        f"/api/approvals/{approval_id}/decision",
        json={"action": "reject", "note": "not ready"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["status"] == "failed", body
    assert body["errors"], "a rejected run must record an error"
    assert any("reject" in err.lower() for err in body["errors"]), body["errors"]


# --------------------------------------------------------------------------- #
# Gate -> rollback -> rolled_back.
# --------------------------------------------------------------------------- #
def test_run_gate_then_rollback(client: TestClient) -> None:
    paused = _start_gated_run(client)
    approval_id = paused["pendingApproval"]["approvalId"]

    resp = client.post(f"/api/approvals/{approval_id}/decision", json={"action": "rollback"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["status"] == "rolled_back", body


# --------------------------------------------------------------------------- #
# A decision on an unknown approval id is a 404 (no live run behind it).
# --------------------------------------------------------------------------- #
def test_decision_unknown_404(client: TestClient) -> None:
    resp = client.post("/api/approvals/apr_nope/decision", json={"action": "approve"})
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# Recovery listing: runs persist, are filterable by status, and fetchable by id.
# --------------------------------------------------------------------------- #
def test_runs_listing(client: TestClient) -> None:
    # Drive a known completed run and a known gated (awaiting_approval) run so the
    # store has representatives of both states regardless of test ordering.
    completed = client.post("/api/workflows/run", json={"task": "Build a landing page"}).json()
    assert completed["status"] == "completed", completed
    completed_id = completed["workflowId"]

    paused = _start_gated_run(client)
    paused_id = paused["workflowId"]

    # Full listing has at least the three runs Phase 7 guarantees.
    resp = client.get("/api/workflows/runs")
    assert resp.status_code == 200
    runs = resp.json()
    assert isinstance(runs, list)
    assert len(runs) >= 3, f"expected >=3 persisted runs, got {len(runs)}"

    # Filtered listing returns only completed runs (and includes our known one).
    resp = client.get("/api/workflows/runs", params={"status": "completed"})
    assert resp.status_code == 200
    completed_runs = resp.json()
    assert completed_runs, "there must be at least one completed run"
    assert all(run["status"] == "completed" for run in completed_runs), completed_runs
    assert completed_id in {run["workflowId"] for run in completed_runs}

    # The awaiting_approval filter (the recovery/resumable set) holds the paused run.
    resp = client.get("/api/workflows/runs", params={"status": "awaiting_approval"})
    assert resp.status_code == 200
    awaiting = resp.json()
    assert all(run["status"] == "awaiting_approval" for run in awaiting), awaiting
    assert paused_id in {run["workflowId"] for run in awaiting}

    # Fetch a known run by id -> 200; unknown id -> 404.
    resp = client.get(f"/api/workflows/runs/{completed_id}")
    assert resp.status_code == 200
    assert resp.json()["workflowId"] == completed_id

    resp = client.get("/api/workflows/runs/wf_does_not_exist")
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# A non-gated task completes immediately with no approval pause.
# --------------------------------------------------------------------------- #
def test_non_gate_completes(client: TestClient) -> None:
    resp = client.post("/api/workflows/run", json={"task": "Build a landing page"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["status"] == "completed", body
    assert body["pendingApproval"] is None
    assert body["agentOutputs"], "a completed run must have agent outputs"
