"""Phase 6 realtime tests: the health snapshot shape + the /ws channel.

The WebSocket tests MUST enter the ``TestClient`` as a context manager so the app
lifespan runs and starts the heartbeat producer. The first two frames over /ws are
the deterministic 'hello' + immediate 'system_health' snapshot (see app.main.ws);
after that, broadcasts (heartbeat health/activity, plus real workflow events) interleave.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.realtime import health_snapshot


def test_health_snapshot() -> None:
    snap = health_snapshot()
    assert isinstance(snap, dict)
    metrics = snap["metrics"]
    assert len(metrics) >= 6

    network = [m for m in metrics if m["label"] == "Network"]
    assert len(network) == 1
    assert network[0]["pct"] is None


def test_ws_hello_and_health() -> None:
    with TestClient(app) as c:
        with c.websocket_connect("/ws") as ws:
            first = ws.receive_json()
            assert first["type"] == "hello"

            second = ws.receive_json()
            assert second["type"] == "system_health"
            assert len(second["payload"]["metrics"]) >= 6


def test_ws_workflow_events() -> None:
    with TestClient(app) as c:
        with c.websocket_connect("/ws") as ws:
            # Drain the deterministic hello + initial health frames.
            assert ws.receive_json()["type"] == "hello"
            assert ws.receive_json()["type"] == "system_health"

            resp = c.post("/api/workflows/run", json={"task": "Build a landing page"})
            assert resp.status_code == 200

            saw_workflow = False
            saw_activity = False
            for _ in range(15):
                event = ws.receive_json()
                etype = event["type"]
                if etype == "workflow":
                    saw_workflow = True
                elif etype == "activity":
                    saw_activity = True
                # system_health / other heartbeat frames may interleave — skip them.
                if saw_workflow and saw_activity:
                    break

            assert saw_workflow, "expected at least one 'workflow' event during the run"
            assert saw_activity, "expected at least one 'activity' event during the run"
