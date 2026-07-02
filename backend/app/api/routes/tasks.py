"""Task routes — scoped to the current user (a task lives inside a project the user owns)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import current_user
from app.schemas.projects import Task, TaskCreate, TaskUpdate
from app.services.project_store import get_project_store

router = APIRouter(tags=["tasks"])


@router.get("", response_model=list[Task])
def list_tasks(
    projectId: str | None = None,
    status: str | None = None,
    current: str = Depends(current_user),
) -> list[Task]:
    # owner_id filter ensures only tasks in the user's projects come back, even if a foreign
    # projectId is supplied.
    return get_project_store().list_tasks(project_id=projectId, status=status, owner_id=current)  # type: ignore[return-value]


@router.post("", response_model=Task)
def create_task(req: TaskCreate, current: str = Depends(current_user)) -> Task:
    store = get_project_store()
    # A task may only be filed under a project the user owns.
    if req.project_id and store.get_project(req.project_id, owner_id=current) is None:
        raise HTTPException(status_code=404, detail=f"No project {req.project_id!r}")
    return store.create_task(  # type: ignore[return-value]
        req.title, project_id=req.project_id, priority=req.priority, agent_id=req.agent_id
    )


@router.patch("/{task_id}", response_model=Task)
def update_task(task_id: str, req: TaskUpdate, current: str = Depends(current_user)) -> Task:
    store = get_project_store()
    if not store.task_owned_by(task_id, current):
        raise HTTPException(status_code=404, detail=f"No task {task_id!r}")
    task = store.update_task(task_id, title=req.title, status=req.status, priority=req.priority)
    if task is None:
        raise HTTPException(status_code=404, detail=f"No task {task_id!r}")
    return task  # type: ignore[return-value]


@router.delete("/{task_id}")
def delete_task(task_id: str, current: str = Depends(current_user)) -> dict[str, bool]:
    store = get_project_store()
    if not store.task_owned_by(task_id, current):
        raise HTTPException(status_code=404, detail=f"No task {task_id!r}")
    if not store.delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"No task {task_id!r}")
    return {"ok": True}
