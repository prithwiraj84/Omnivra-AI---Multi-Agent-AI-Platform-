"""Typed LangGraph state for the Omnivra orchestration graph.

``OmnivraState`` is the channel dict threaded through every node. ``recursion_count``
backs the kill switch; ``status`` tracks the workflow lifecycle; ``pending_approval``
holds the human-gate payload when the graph interrupts.
"""
from __future__ import annotations

import operator
from enum import Enum
from typing import Annotated, Any, TypedDict


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"          # kill switch tripped
    ROLLED_BACK = "rolled_back"


class AgentOutput(TypedDict, total=False):
    agent_id: str
    content: str
    artifacts: list[str]         # workspace-relative artifact paths
    tokens: int
    ok: bool


class ApprovalRequest(TypedDict, total=False):
    approval_id: str
    kind: str                    # 'content' | 'final_code' | 'presentation_export'
    summary: str
    artifacts: list[str]
    requested_by: str            # agent id


class OmnivraState(TypedDict, total=False):
    """The graph state object. ``Annotated[..., operator.add]`` channels accumulate."""

    workflow_id: str
    project_id: str
    task: str
    status: WorkflowStatus

    # Kill switch counter. Incremented on each orchestration loop; guarded by
    # app.graph.kill_switch.check_kill_switch against settings.max_recursion.
    recursion_count: int

    plan: list[str]
    current_agent: str
    delegations: Annotated[list[str], operator.add]
    agent_outputs: Annotated[list[AgentOutput], operator.add]

    pending_approval: ApprovalRequest | None
    manifest_ref: str            # checkpoint/manifest id for resume
    errors: Annotated[list[str], operator.add]
    result: dict[str, Any]


def new_state(*, workflow_id: str, project_id: str, task: str) -> OmnivraState:
    """Construct an initial state for a new workflow run."""
    return OmnivraState(
        workflow_id=workflow_id,
        project_id=project_id,
        task=task,
        status=WorkflowStatus.PENDING,
        recursion_count=0,
        plan=[],
        current_agent="ceo-manager",
        delegations=[],
        agent_outputs=[],
        pending_approval=None,
        manifest_ref="",
        errors=[],
        result={},
    )
