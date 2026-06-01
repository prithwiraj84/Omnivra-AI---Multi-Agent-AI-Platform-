"""REST API tests for the Omnivra dashboard endpoints (mounted at ``/api``).

Exercises every route module wired through :mod:`app.api.router` and asserts the
JSON is camelCase (FastAPI serializes ``response_model`` with ``by_alias=True``)
so the body matches the frontend TypeScript DTO types field-for-field.

Reuses the session-scoped ``client`` fixture from :mod:`tests.conftest`, which
wraps ``app.main.app`` in a ``TestClient`` with lifespan run.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

# Provider keys allowed on the wire (mirrors providers.registry.PROVIDER_NAMES).
VALID_PROVIDERS = {"google_ai", "openrouter", "groq", "huggingface"}

# Every key the aggregate dashboard payload must expose, in camelCase.
DASHBOARD_KEYS = {
    "stats",
    "agents",
    "systemOps",
    "workflows",
    "taskExecution",
    "taskExecutionSeries",
    "taskDistribution",
    "totalTasks",
    "activity",
    "approvals",
    "totalPendingApprovals",
    "systemHealth",
    "providerUsage",
    "modelUsage",
    "mediaServices",
    "achievements",
}


def test_dashboard_returns_full_camelcase_payload(client: TestClient) -> None:
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    body = resp.json()

    # Exactly the contract keys, all camelCase.
    assert DASHBOARD_KEYS.issubset(body.keys())

    # Agents come from the repo (registry/Supabase) — pinned counts.
    assert len(body["agents"]) == 18
    assert len(body["systemOps"]) == 5
    # Operational totals are now computed LIVE from the running system (cp-0022),
    # not seed constants — assert the contract/type, not a fixed value.
    assert isinstance(body["totalTasks"], int) and body["totalTasks"] >= 0
    assert isinstance(body["totalPendingApprovals"], int) and body["totalPendingApprovals"] >= 0


def test_dashboard_agents_are_camelcase(client: TestClient) -> None:
    body = client.get("/api/dashboard").json()
    first = body["agents"][0]
    # camelCase aliases present, snake_case absent.
    assert "providerLabel" in first
    assert "modelLabel" in first
    assert "provider_label" not in first
    assert "model_label" not in first


def test_list_agents_returns_all_23(client: TestClient) -> None:
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) == 23
    for agent in agents:
        assert agent["providerLabel"]
        assert agent["modelLabel"]
        assert agent["accent"]
        assert agent["provider"] in VALID_PROVIDERS


def test_get_agent_by_id(client: TestClient) -> None:
    resp = client.get("/api/agents/ceo-manager")
    assert resp.status_code == 200
    agent = resp.json()
    assert agent["id"] == "ceo-manager"
    assert agent["provider"] == "google_ai"
    assert agent["model"] == "gemini-3.1-flash-lite"
    assert agent["providerLabel"] == "Google AI Studio"


def test_get_agent_unknown_returns_404(client: TestClient) -> None:
    resp = client.get("/api/agents/nope")
    assert resp.status_code == 404


def test_list_workflows(client: TestClient) -> None:
    resp = client.get("/api/workflows")
    assert resp.status_code == 200
    workflows = resp.json()
    assert isinstance(workflows, list)
    assert len(workflows) >= 5
    first = workflows[0]
    assert "progress" in first
    assert "accent" in first
    assert "status" in first


def test_list_approvals(client: TestClient) -> None:
    resp = client.get("/api/approvals")
    assert resp.status_code == 200
    approvals = resp.json()
    assert isinstance(approvals, list)
    assert len(approvals) >= 4
    assert {"id", "title", "source", "priority", "icon", "accent"}.issubset(approvals[0].keys())


def test_list_activity(client: TestClient) -> None:
    resp = client.get("/api/activity")
    assert resp.status_code == 200
    activity = resp.json()
    assert isinstance(activity, list)
    assert len(activity) >= 6
    assert {"id", "agent", "action", "time", "accent", "icon"}.issubset(activity[0].keys())


def test_system_health(client: TestClient) -> None:
    resp = client.get("/api/system/health")
    assert resp.status_code == 200
    health = resp.json()
    assert isinstance(health, list)
    assert len(health) >= 6
    labels = {metric["label"] for metric in health}
    assert "Network" in labels


def test_approval_decision_unknown_returns_404(client: TestClient) -> None:
    # Phase 7: a decision only resolves a real paused workflow. The seed approval
    # 'ap1' has no live run behind it, so the resume endpoint returns 404.
    # (The full run->gate->resume flow is covered in test_approval_resume.py.)
    resp = client.post("/api/approvals/ap1/decision", json={"action": "approve"})
    assert resp.status_code == 404
