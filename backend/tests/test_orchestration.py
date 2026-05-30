"""Phase 5 orchestration tests: providers (offline stub), planner, the CEO->dept
workflow service, the approval gate, the kill switch wiring, and the run endpoint.

Everything runs offline: with no provider API keys in the test env the providers
return deterministic stubs, so the whole LangGraph orchestration is reproducible.
Async service/graph paths are driven with ``asyncio.run``; the HTTP path reuses
the session-scoped ``client`` fixture from :mod:`tests.conftest`.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.agents.registry import AGENT_REGISTRY
from app.agents.runner import run_agent
from app.graph.kill_switch import check_kill_switch
from app.graph.planner import plan_delegations
from app.graph.state import WorkflowStatus, new_state
from app.providers.registry import get_provider_registry
from app.services.orchestrator import run_workflow


# --------------------------------------------------------------------------- #
# Providers run offline in deterministic STUB mode (no keys in the test env).
# --------------------------------------------------------------------------- #
def test_providers_offline_stub() -> None:
    registry = get_provider_registry()

    # No API keys configured under test -> every provider reports unconfigured.
    status = registry.status()
    assert status, "provider status map must not be empty"
    assert all(value is False for value in status.values()), status

    # A stub agent run still succeeds with deterministic stub content.
    out = asyncio.run(run_agent("ceo-manager", "hi", registry=registry))
    assert out["ok"] is True
    assert out["content"].startswith("[stub")


# --------------------------------------------------------------------------- #
# Planner: ordered, architect-first, bounded, all-known, with a sane fallback.
# --------------------------------------------------------------------------- #
def test_plan_delegations_design_and_api() -> None:
    plan = plan_delegations("Design the UI and build the API", "")

    assert plan[0] == "solution-architect"
    assert 2 <= len(plan) <= 5
    assert all(agent_id in AGENT_REGISTRY for agent_id in plan)
    # No duplicates in the ordered plan.
    assert len(plan) == len(set(plan))


def test_plan_delegations_empty_task_falls_back() -> None:
    plan = plan_delegations("", "")

    # Empty-ish task still yields a valid, architect-first default plan.
    assert plan[0] == "solution-architect"
    assert 2 <= len(plan) <= 5
    assert all(agent_id in AGENT_REGISTRY for agent_id in plan)


# --------------------------------------------------------------------------- #
# run_workflow: happy path drives CEO -> delegate -> finalize to COMPLETED.
# --------------------------------------------------------------------------- #
def test_run_workflow_happy_path() -> None:
    result = asyncio.run(run_workflow("Build a landing page and REST API"))

    assert result.status == "completed"
    assert len(result.agent_outputs) >= 2
    assert result.recursion_count >= 1
    assert result.plan, "a completed workflow must have produced a plan"
    assert result.pending_approval is None


# --------------------------------------------------------------------------- #
# Approval gate: a gated task interrupts with a pending approval payload.
# --------------------------------------------------------------------------- #
def test_run_workflow_approval_gate() -> None:
    result = asyncio.run(run_workflow("Publish the investor presentation"))

    assert result.status == "awaiting_approval"
    assert result.pending_approval is not None
    assert result.pending_approval.approval_id


# --------------------------------------------------------------------------- #
# Kill switch wiring: recursion_count over the limit forces STOPPED.
# --------------------------------------------------------------------------- #
def test_kill_switch_wiring() -> None:
    state = new_state(workflow_id="wf-kill", project_id="proj", task="loop forever")
    state["recursion_count"] = 5

    delta = check_kill_switch(state)
    assert delta["status"] == WorkflowStatus.STOPPED


# --------------------------------------------------------------------------- #
# Endpoint: POST /api/workflows/run returns a camelCase RunResult body.
# --------------------------------------------------------------------------- #
def test_run_endpoint(client: TestClient) -> None:
    resp = client.post("/api/workflows/run", json={"task": "Build a landing page"})
    assert resp.status_code == 200

    body = resp.json()
    assert body["workflowId"]
    assert body["status"] == "completed"
    assert isinstance(body["agentOutputs"], list)
    assert body["agentOutputs"], "agentOutputs must be a non-empty list"
    assert "recursionCount" in body
