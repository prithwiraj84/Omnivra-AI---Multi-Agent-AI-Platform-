"""Workflow routes: list the active workflow items and run the orchestrator."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api.deps import get_repo, require_user
from app.db.repositories import DashboardRepository
from app.schemas import RunRequest, RunResult
from app.services.orchestrator import run_workflow
from app.services.workflow_store import get_workflow_store

router = APIRouter(tags=["workflows"])


@router.get("", response_model=list[schemas.WorkflowItem])
def list_workflows(repo: DashboardRepository = Depends(get_repo)) -> list[schemas.WorkflowItem]:
    """Return the active workflow items."""
    return repo.list_workflows()


@router.post("/run", response_model=RunResult)
async def run(req: RunRequest, _user: str = Depends(require_user)) -> RunResult:
    """Run the CEO->department orchestration graph for one task."""
    return await run_workflow(req.task, req.project_id)


@router.get("/runs", response_model=list[RunResult])
def list_runs(status: str | None = None) -> list[RunResult]:
    """List persisted workflow runs (optionally filtered by status, e.g. awaiting_approval).

    Used by the Recovery view to surface paused/interrupted runs that can be resumed.
    """
    return get_workflow_store().list(status=status)


@router.get("/runs/{workflow_id}", response_model=RunResult)
def get_run(workflow_id: str) -> RunResult:
    """Fetch one persisted workflow run by id."""
    run = get_workflow_store().get(workflow_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No workflow run {workflow_id!r}")
    return run
