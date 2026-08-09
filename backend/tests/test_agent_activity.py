"""Live agent activity (cp-0069): "working" must mean working, wherever the call came from.

The bug this pins: the dashboard derived agent status ONLY from LangGraph workflow runs, but
Document Studio and Social Studio invoke agents directly with no run behind them — so the whole
roster read "Idle" while a document was visibly generating. Activity is now registered at
`agents.runner.run_agent`, the single funnel every LLM call passes through.
"""
from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.agents.runner import run_agent
from app.providers.registry import get_provider_registry
from app.services import agent_activity


def _base_payload():
    """The un-live dashboard the route starts from (registry/Supabase agents + seed shells)."""
    from app.api.deps import get_repo

    return get_repo().get_dashboard()


@pytest.fixture(autouse=True)
def _clean() -> None:
    agent_activity.reset()
    yield
    agent_activity.reset()


# --- the registry itself ------------------------------------------------------------------


def test_begin_end_report_transitions_only() -> None:
    """Only 0->1 and 1->0 return True, so the socket isn't spammed by concurrent calls to the
    same agent (per-scene narration fans out several at once)."""
    assert agent_activity.begin("reel-automation") is True
    assert agent_activity.begin("reel-automation") is False
    assert agent_activity.active_agents() == {"reel-automation"}
    assert agent_activity.end("reel-automation") is False, "still one call in flight"
    assert agent_activity.end("reel-automation") is True
    assert agent_activity.active_agents() == set()


def test_unbalanced_end_is_harmless() -> None:
    assert agent_activity.end("never-started") is False
    assert agent_activity.active_agents() == set()


def test_activity_is_scoped_per_owner() -> None:
    """One user's in-flight agents must not light up another user's dashboard."""
    agent_activity.begin("reel-automation", "user-a")
    assert agent_activity.active_agents("user-a") == {"reel-automation"}
    assert agent_activity.active_agents("user-b") == set()
    agent_activity.end("reel-automation", "user-a")
    assert agent_activity.active_agents("user-a") == set()


def test_stale_entries_stop_counting(monkeypatch) -> None:
    """A hard kill mid-call would otherwise pin an agent to 'working' forever."""
    import time

    agent_activity.begin("ceo-manager", "u")
    assert agent_activity.active_agents("u") == {"ceo-manager"}
    monkeypatch.setattr(time, "monotonic", lambda: time.perf_counter() + agent_activity.STALE_AFTER_SECONDS + 60)
    assert agent_activity.active_agents("u") == set()


def test_working_contextmanager_releases_on_error() -> None:
    with pytest.raises(RuntimeError):
        with agent_activity.working("qa-engineer", "u"):
            assert agent_activity.active_agents("u") == {"qa-engineer"}
            raise RuntimeError("boom")
    assert agent_activity.active_agents("u") == set()


# --- the funnel ---------------------------------------------------------------------------


def test_run_agent_marks_the_agent_working_for_the_duration() -> None:
    """The whole point: a DIRECT agent call (Document/Social Studio) registers as working."""
    seen: list[set[str]] = []

    class _Provider:
        is_configured = False

        async def complete(self, _req):  # noqa: ANN001
            seen.append(agent_activity.active_agents())
            from app.providers._compat import make_stub_response

            return make_stub_response(_req, "stub")

    class _Registry:
        @staticmethod
        def get(_name):  # noqa: ANN001
            return _Provider()

    out = asyncio.run(run_agent("documentation-agent", "write a doc", registry=_Registry()))
    assert out["ok"]
    assert seen == [{"documentation-agent"}], "must be marked working DURING the call"
    assert agent_activity.active_agents() == set(), "and released afterwards"


def test_run_agent_releases_even_when_the_provider_explodes() -> None:
    """A crashed agent must not stay 'working' on the dashboard."""

    class _Boom:
        is_configured = False

        async def complete(self, _req):  # noqa: ANN001
            raise RuntimeError("provider down")

    class _Registry:
        @staticmethod
        def get(_name):  # noqa: ANN001
            return _Boom()

    out = asyncio.run(run_agent("qa-engineer", "test", registry=_Registry()))
    assert out["ok"] is False
    assert agent_activity.active_agents() == set()


def test_run_agent_releases_on_cancellation() -> None:
    """Cancelling a generation (client disconnect, shutdown) must release the agent too."""

    class _Hang:
        is_configured = False

        async def complete(self, _req):  # noqa: ANN001
            await asyncio.sleep(30)

    class _Registry:
        @staticmethod
        def get(_name):  # noqa: ANN001
            return _Hang()

    async def go() -> None:
        task = asyncio.create_task(run_agent("seo-researcher", "x", registry=_Registry()))
        await asyncio.sleep(0.05)
        assert agent_activity.active_agents() == {"seo-researcher"}
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(go())
    assert agent_activity.active_agents() == set()


# --- what the dashboard actually shows ----------------------------------------------------


def test_dashboard_shows_an_in_flight_agent_as_working() -> None:
    """The reported symptom, end to end: an agent working with NO workflow run behind it used
    to render as Idle for the entire generation."""
    from app.services.dashboard_live import build_live_dashboard

    base = _base_payload()

    before = build_live_dashboard(base)
    assert all(a.status == "idle" for a in before.agents), "nothing running yet"

    agent_activity.begin("documentation-agent")
    try:
        during = build_live_dashboard(base)
        by_id = {a.id: a.status for a in during.agents}
        assert by_id["documentation-agent"] == "working"
        assert by_id["qa-engineer"] == "idle", "only the agent actually running turns active"
        assert any("1 active" in (s.sub or "") for s in during.stats), "the Agents stat must count it"
    finally:
        agent_activity.end("documentation-agent")

    after = build_live_dashboard(base)
    assert all(a.status == "idle" for a in after.agents)


def test_dashboard_endpoint_reflects_live_activity(client: TestClient) -> None:
    agent_activity.begin("reel-automation")
    try:
        # The endpoint caches for a beat; ask for a fresh build the same way a poll would.
        body = client.get("/api/dashboard").json()
        statuses = {a["id"]: a["status"] for a in body["agents"] + body.get("systemOps", [])}
        assert statuses.get("reel-automation") == "working", statuses.get("reel-automation")
    finally:
        agent_activity.end("reel-automation")


def test_system_ops_agents_also_report_live_status() -> None:
    from app.services.dashboard_live import build_live_dashboard

    base = _base_payload()
    _primary, system = __import__("app.data.seed", fromlist=["seed_agents"]).seed_agents()
    if not system:
        pytest.skip("no system-ops agents in the roster")
    target = system[0].id
    agent_activity.begin(target)
    try:
        out = build_live_dashboard(base)
        assert {a.id: a.status for a in out.system_ops}[target] == "working"
    finally:
        agent_activity.end(target)


def test_dashboard_cache_does_not_hide_a_status_change(client: TestClient, monkeypatch) -> None:
    """With the short-TTL cache ON, a start/stop must still be visible immediately.

    A document can be generated in less time than the TTL, so a purely time-based cache could
    render the whole thing as if nothing ever ran.
    """
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "dashboard_cache_ttl", 30.0, raising=False)

    def statuses() -> dict:
        b = client.get("/api/dashboard").json()
        return {a["id"]: a["status"] for a in b["agents"] + b.get("systemOps", [])}

    assert statuses().get("reel-automation") == "idle"  # warms the cache

    agent_activity.begin("reel-automation")
    try:
        assert statuses().get("reel-automation") == "working", "the cache must not mask the start"
    finally:
        agent_activity.end("reel-automation")

    assert statuses().get("reel-automation") == "idle", "nor the finish"


def test_agent_activity_reaches_connected_dashboards() -> None:
    """The realtime leg: a browser must be TOLD an agent started, not have to poll for it.

    Without this frame the roster only updates on the next poll — which for a short generation
    can land entirely after the work is over.
    """
    from app.main import app

    with TestClient(app) as c:
        with c.websocket_connect("/ws") as ws:
            assert ws.receive_json()["type"] == "hello"
            assert ws.receive_json()["type"] == "system_health"

            # A document draft calls the documentation agent directly — no workflow involved.
            resp = c.post("/api/documents/generate", json={"prompt": "one page on testing", "format": "docx"})
            assert resp.status_code in (200, 202), resp.text

            working = idle = False
            for _ in range(40):
                event = ws.receive_json()
                if event["type"] != "agent_activity":
                    continue
                if event["payload"]["status"] == "working":
                    working = True
                elif event["payload"]["status"] == "idle":
                    idle = True
                if working and idle:
                    break
            assert working, "no 'working' frame was broadcast when the agent started"
            assert idle, "no 'idle' frame was broadcast when the agent finished"
