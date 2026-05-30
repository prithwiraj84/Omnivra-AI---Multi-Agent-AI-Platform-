"""Human Approval Gate model stub.

Before publishing content, finalizing code artifacts, or exporting presentations,
the graph interrupts and emits an :class:`ApprovalGate`. A human responds with an
:class:`ApprovalDecision` (APPROVE / REJECT / RETRY / ROLLBACK) via the
/api/approvals route or the /ws channel, and the workflow resumes from the
checkpoint. Phase 3 binds these models to the LangGraph ``interrupt`` mechanism.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ApprovalKind(str, Enum):
    CONTENT = "content"
    FINAL_CODE = "final_code"
    PRESENTATION_EXPORT = "presentation_export"


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    RETRY = "retry"
    ROLLBACK = "rollback"


class ApprovalGate(BaseModel):
    """A pending approval surfaced to the user (Pending Approvals card)."""

    approval_id: str = Field(default_factory=lambda: f"apr_{uuid4().hex[:12]}")
    workflow_id: str
    kind: ApprovalKind
    title: str
    summary: str
    artifacts: list[str] = Field(default_factory=list)  # workspace-relative paths
    requested_by: str                                    # agent id
    priority: str = "medium"                             # high | medium
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalResolution(BaseModel):
    """The human response that resumes the workflow."""

    approval_id: str
    decision: ApprovalDecision
    note: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
