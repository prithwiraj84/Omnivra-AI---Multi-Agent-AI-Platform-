"""Kill switch for the orchestration graph.

LangGraph has its own ``recursion_limit``, but Omnivra also tracks a domain-level
``recursion_count`` in state so the CEO delegation loop cannot spin forever. When
the count exceeds ``settings.max_recursion`` (default 3) the workflow is marked
STOPPED and downstream nodes short-circuit.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import logger
from app.graph.state import OmnivraState, WorkflowStatus


class KillSwitchTripped(Exception):
    """Raised (or signalled via state) when recursion_count exceeds the limit."""


def increment_recursion(state: OmnivraState) -> int:
    """Increment and return the new recursion count."""
    count = int(state.get("recursion_count", 0)) + 1
    state["recursion_count"] = count
    return count


def is_tripped(state: OmnivraState) -> bool:
    """True when recursion_count exceeds the configured maximum."""
    return int(state.get("recursion_count", 0)) > get_settings().max_recursion


def check_kill_switch(state: OmnivraState) -> OmnivraState:
    """Graph guard node: stop the workflow if the kill switch tripped.

    Returns a state delta. Use as a conditional edge source: route to END when
    ``state['status'] == WorkflowStatus.STOPPED``.
    """
    limit = get_settings().max_recursion
    count = int(state.get("recursion_count", 0))
    if count > limit:
        logger.error(
            "Kill switch tripped for workflow {}: recursion_count={} > max={}",
            state.get("workflow_id"), count, limit,
        )
        return OmnivraState(
            status=WorkflowStatus.STOPPED,
            errors=[f"Kill switch: recursion_count {count} exceeded max {limit}"],
        )
    return OmnivraState(status=state.get("status", WorkflowStatus.RUNNING))
