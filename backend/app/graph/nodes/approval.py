"""Approval node — gate sensitive workflows behind a real human-in-the-loop pause.

Tasks that publish, deploy, export, release, go live, produce a presentation, or
ask for a final deliverable call LangGraph ``interrupt()``, suspending the run with
a ``pending_approval`` payload. A human decision (approve / reject / retry / rollback)
resumes the graph via ``Command(resume={"action": ...})``; the resumed ``interrupt()``
return value selects the branch. All other workflows pass straight through to finalize.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable
from uuid import uuid4

from langgraph.types import interrupt

from app.core.logging import logger
from app.graph.state import OmnivraState, WorkflowStatus

ApprovalNode = Callable[[OmnivraState], Awaitable[OmnivraState]]

_APPROVAL_KEYWORDS = ("publish", "deploy", "export", "release", "go live", "presentation", "final")


def needs_approval(task: str) -> bool:
    """True when ``task`` mentions a gated action requiring human approval."""
    lowered = (task or "").lower()
    return any(kw in lowered for kw in _APPROVAL_KEYWORDS)


def make_approval_node() -> ApprovalNode:
    """Build the async approval node (no provider dependency)."""

    async def approval_node(state: OmnivraState) -> OmnivraState:
        task = state.get("task", "")
        if not needs_approval(task):
            return OmnivraState(status=WorkflowStatus.RUNNING)

        approval_id = f"apr_{uuid4().hex[:12]}"
        logger.info("[approval] gating workflow {} -> {}", state.get("workflow_id"), approval_id)

        # Suspends the run on first pass; returns the human's decision dict on resume.
        decision: Any = interrupt(
            {
                "approval_id": approval_id,
                "kind": "final_code",
                "summary": f"Approval required before completing: {task}",
                "requested_by": "ceo-manager",
                "priority": "high",
            }
        )

        action = decision.get("action", "approve") if isinstance(decision, dict) else str(decision or "approve")
        note = decision.get("note") if isinstance(decision, dict) else None
        logger.info("[approval] workflow {} resumed with action={}", state.get("workflow_id"), action)

        if action in ("approve", "retry"):
            return OmnivraState(status=WorkflowStatus.RUNNING)
        if action == "reject":
            return OmnivraState(status=WorkflowStatus.FAILED, errors=[f"Rejected by human{f': {note}' if note else ''}"])
        if action == "rollback":
            return OmnivraState(status=WorkflowStatus.ROLLED_BACK, errors=["Rolled back by human"])
        return OmnivraState(status=WorkflowStatus.RUNNING)

    return approval_node
