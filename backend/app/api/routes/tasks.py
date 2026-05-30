"""Task routes: list (filter by projectId/status) / create / update / delete."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_user
from app.schemas.projects import Task, TaskCreate, TaskUpdate
from app.services.project_store import get_project_store

router = APIRouter(tags=["tasks"])


@router.get("", response_model=list[Task])
def list_tasks(projectId: str | None = None, status: str | None = None) -> list[Task]:
    return get_project_store().list_tasks(project_id=projectId, status=status)  # type: ignore[return-value]


@router.post("", response_model=Task)
def create_task(req: TaskCreate, _user: str = Depends(require_user)) -> Task:
    return get_project_store().create_task(  # type: ignore[return-value]
        req.title, project_id=req.project_id, priority=req.priority, agent_id=req.agent_id
    )


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: str, req: TaskUpdate, _user: str = Depends(require_user)) -> Task:
    task = get_project_store().update_task(task_id, title=req.title, status=req.status, priority=req.priority)
    if task is None:
        raise HTTPException(status_code=404, detail=f"No task {task_id!r}")
    return task  # type: ignore[return-value]


@router.delete("/{task_id}")
def delete_task(task_id: str, _user: str = Depends(require_user)) -> dict[str, bool]:
    if not get_project_store().delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"No task {task_id!r}")
    return {"ok": True}
