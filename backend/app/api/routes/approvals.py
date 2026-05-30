"""Approval routes: list pending approvals and resume a paused workflow on a decision.

POST /{approval_id}/decision actually re-enters the paused LangGraph run via
app.services.orchestrator.resume_workflow — approve/retry continue to completion,
reject -> FAILED, rollback -> ROLLED_BACK.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import schemas
from app.api.deps import get_repo, require_user
from app.db.repositories import DashboardRepository
from app.schemas import RunResult
from app.services.orchestrator import resume_workflow
from app.services.workflow_store import get_workflow_store

router = APIRouter(tags=["approvals"])

ApprovalAction = Literal["approve", "reject", "retry", "rollback"]


class ApprovalDecision(BaseModel):
    action: ApprovalAction
    note: str | None = None


@router.get("", response_model=list[schemas.ApprovalItem])
def list_approvals(repo: DashboardRepository = Depends(get_repo)) -> list[schemas.ApprovalItem]:
    """Return the (seed) pending approval items shown on the dashboard."""
    return repo.list_approvals()


@router.post("/{approval_id}/decision", response_model=RunResult)
async def submit_decision(approval_id: str, decision: ApprovalDecision, _user: str = Depends(require_user)) -> RunResult:
    """Resume the workflow gated by ``approval_id`` with the human decision."""
    run = get_workflow_store().find_by_approval(approval_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No pending workflow for approval {approval_id!r}")
    return await resume_workflow(run.workflow_id, decision.action, decision.note)
