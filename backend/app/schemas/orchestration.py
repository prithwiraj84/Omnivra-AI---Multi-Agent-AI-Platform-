"""Schemas for the workflow-run (orchestration) API. camelCase on the wire."""
from __future__ import annotations

from app.schemas.dashboard import CamelModel


class RunRequest(CamelModel):
    task: str
    # The active project is taken from the X-Project-Id header (get_project_id), not
    # the body, so a run always lands in the project the UI is scoped to.


class AgentRunOutput(CamelModel):
    agent_id: str
    content: str
    ok: bool
    tokens: int = 0
    artifacts: list[str] = []


class PendingApproval(CamelModel):
    approval_id: str
    kind: str
    summary: str
    requested_by: str


class RunResult(CamelModel):
    """Result of running the CEO->department orchestration graph for one task."""

    workflow_id: str
    project_id: str | None = None
    status: str  # pending|planning|running|awaiting_approval|completed|failed|stopped|rolled_back
    task: str
    plan: list[str] = []
    delegations: list[str] = []
    current_agent: str | None = None  # the agent CURRENTLY executing (live status while 'running'); None when idle/terminal
    agent_outputs: list[AgentRunOutput] = []
    recursion_count: int = 0
    result: dict = {}
    errors: list[str] = []
    pending_approval: PendingApproval | None = None
