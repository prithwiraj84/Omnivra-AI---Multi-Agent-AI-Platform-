"""Finalize node — mark the workflow COMPLETED unless it was stopped or gated.

If the kill switch tripped (STOPPED) or the approval node interrupted the run
(AWAITING_APPROVAL), the workflow is already in a terminal/paused state and is
returned unchanged. Otherwise a result summary is produced.
"""
from __future__ import annotations

from app.graph.state import OmnivraState, WorkflowStatus


async def finalize_node(state: OmnivraState) -> OmnivraState:
    """Produce the final result, or pass through stopped/awaiting-approval states."""
    status = state.get("status")
    if status in (WorkflowStatus.STOPPED, WorkflowStatus.AWAITING_APPROVAL):
        return state

    agent_outputs = list(state.get("agent_outputs", []))
    return OmnivraState(
        status=WorkflowStatus.COMPLETED,
        result={
            "summary": f"{len(agent_outputs)} agents responded",
            "agents": [o.get("agent_id") for o in agent_outputs],
            "ok": True,
        },
    )
