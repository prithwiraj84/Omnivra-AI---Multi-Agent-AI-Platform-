"""Approval routes: list pending approvals and resume a paused workflow on a decision.

POST /{approval_id}/decision actually re-enters the paused LangGraph run via
app.services.orchestrator.resume_workflow — approve/retry continue to completion,
reject -> FAILED, rollback -> ROLLED_BACK.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app import schemas
from app.api.deps import current_user, get_repo
from app.db.repositories import DashboardRepository
from app.schemas import RunResult
from app.services.orchestrator import resume_workflow
from app.services.project_store import get_project_store
from app.services.workflow_store import find_by_approval, get_workflow_store

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
def submit_decision(
    approval_id: str,
    decision: ApprovalDecision,
    background_tasks: BackgroundTasks,
    current: str = Depends(current_user),
) -> RunResult:
    """Resume the workflow gated by ``approval_id`` with the human decision; returns IMMEDIATELY.

    Resuming re-enters the LangGraph run (approve/retry continue to completion — many seconds,
    past the UI timeout), so we mark the run 'running' and resume in a BackgroundTask. The client
    polls the awaiting/runs sets (and watches /ws) for the terminal state. The pending run is
    located across all projects (the approval id alone doesn't name a project), then checked to
    belong to the current user so no one can decide on another user's workflow.
    """
    located = find_by_approval(approval_id)
    if located is None:
        raise HTTPException(status_code=404, detail=f"No pending workflow for approval {approval_id!r}")
    project_id, run = located
    if not get_project_store().owns(project_id, current):
        raise HTTPException(status_code=404, detail=f"No pending workflow for approval {approval_id!r}")
    # Idempotency guard: find_by_approval matches on pending_approval.approval_id (no status filter),
    # so a double-click / second tab could re-locate a run we already flipped. Only an actually-awaiting
    # run may be decided; otherwise return 409 rather than scheduling a duplicate resume on the same
    # (already-consumed) LangGraph checkpoint.
    if run.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail=f"Approval {approval_id!r} is no longer pending (run status: {run.status})")
    run.status = "running"  # leave the awaiting set immediately; the bg resume reaches the terminal state
    run.pending_approval = None  # clear the handle so a retried decision no longer matches via find_by_approval
    get_workflow_store(project_id).save(run)
    background_tasks.add_task(resume_workflow, run.workflow_id, decision.action, decision.note, project_id)
    return run
