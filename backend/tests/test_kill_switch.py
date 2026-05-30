"""The kill switch must stop a runaway delegation loop (recursion_count > max)."""
from __future__ import annotations

from app.core.config import get_settings
from app.graph.kill_switch import check_kill_switch, increment_recursion, is_tripped
from app.graph.state import WorkflowStatus, new_state


def _fresh_state():
    return new_state(workflow_id="wf-test", project_id="proj-test", task="build something")


def test_not_tripped_within_limit() -> None:
    state = _fresh_state()
    limit = get_settings().max_recursion
    for _ in range(limit):  # increment up to the limit (==3 by default)
        increment_recursion(state)
    assert state["recursion_count"] == limit
    assert is_tripped(state) is False
    assert check_kill_switch(state)["status"] != WorkflowStatus.STOPPED


def test_tripped_above_limit() -> None:
    state = _fresh_state()
    limit = get_settings().max_recursion
    for _ in range(limit + 1):  # one past the limit
        increment_recursion(state)
    assert state["recursion_count"] == limit + 1
    assert is_tripped(state) is True

    delta = check_kill_switch(state)
    assert delta["status"] == WorkflowStatus.STOPPED
    assert delta["errors"], "a stopped workflow must record why"


def test_increment_returns_new_count() -> None:
    state = _fresh_state()
    assert increment_recursion(state) == 1
    assert increment_recursion(state) == 2
