"""Workflow routes: list the active workflow items and run the orchestrator."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app import schemas
from app.api.deps import get_project_id, get_repo, require_user
from app.db.repositories import DashboardRepository
from app.schemas import RunRequest, RunResult
from app.services.orchestrator import begin_run, run_workflow
from app.services.workflow_store import get_workflow_store

router = APIRouter(tags=["workflows"])


@router.get("", response_model=list[schemas.WorkflowItem])
def list_workflows(repo: DashboardRepository = Depends(get_repo)) -> list[schemas.WorkflowItem]:
    """Return the active workflow items."""
    return repo.list_workflows()


@router.post("/run", response_model=RunResult)
def run(
    req: RunRequest,
    background_tasks: BackgroundTasks,
    project_id: str = Depends(get_project_id),
    _user: str = Depends(require_user),
) -> RunResult:
    """Kick off the CEO->department orchestration for one task; returns IMMEDIATELY.

    A real multi-agent run takes many seconds (well past the UI request timeout), so we persist
    a 'running' record and run the graph in a BackgroundTask. The response carries the workflow id
    + status 'running'; the client polls GET /workflows/runs/{id} (and watches /ws) until terminal.
    The project is the active one (X-Project-Id / ?projectId=), validated by get_project_id.
    """
    pending = begin_run(req.task, project_id)
    background_tasks.add_task(run_workflow, req.task, project_id, pending.workflow_id)
    return pending


@router.get("/runs", response_model=list[RunResult])
def list_runs(status: str | None = None, project_id: str = Depends(get_project_id)) -> list[RunResult]:
    """List the active project's persisted workflow runs (optionally filtered by status).

    Used by the Recovery view to surface paused/interrupted runs that can be resumed.
    """
    return get_workflow_store(project_id).list(status=status)


@router.get("/runs/{workflow_id}", response_model=RunResult)
def get_run(workflow_id: str, project_id: str = Depends(get_project_id)) -> RunResult:
    """Fetch one persisted workflow run by id within the active project."""
    run = get_workflow_store(project_id).get(workflow_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No workflow run {workflow_id!r}")
    return run
