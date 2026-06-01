"""The dashboard payload is computed LIVE from the running system (cp-0022),
not static seed demo data. After a real workflow run, the aggregate reflects it."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.agents.registry import AGENT_REGISTRY


def test_dashboard_reflects_live_data(client: TestClient) -> None:
    # Run a workflow so there is real activity (agents invoked -> usage; a run recorded).
    assert client.post("/api/workflows/run", json={"task": "Build a thing"}).status_code == 200

    body = client.get("/api/dashboard").json()
    assert body["agents"], "agents must still be present"

    stats = {s["label"]: s["value"] for s in body["stats"]}
    # Real, computed values — not the seed demo constants.
    assert stats["Agents"] == str(len(AGENT_REGISTRY))
    assert stats["Workflow Runs"].isdigit() and int(stats["Workflow Runs"]) >= 1
    assert int(stats["LLM Calls"]) >= 1  # the run invoked agents -> recorded session usage

    # System health shows real signals (not the seed CPU/Memory bars).
    labels = {h["label"] for h in body["systemHealth"]}
    assert {"Providers Online", "Workflow Runs", "Memory Items"}.issubset(labels)

    # Achievements are computed from real milestones (mention agents/runs).
    titles = " ".join(a["title"] for a in body["achievements"])
    assert "Agents Registered" in titles
