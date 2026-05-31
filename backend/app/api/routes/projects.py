"""Project routes: list / create / get / delete (mutations require auth when enabled)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_user
from app.schemas.projects import Project, ProjectCreate
from app.services.project_store import get_project_store
from app.workspace_fs.paths import DEFAULT_PROJECT

router = APIRouter(tags=["projects"])


@router.get("", response_model=list[Project])
def list_projects() -> list[Project]:
    return get_project_store().list_projects()  # type: ignore[return-value]


@router.post("", response_model=Project)
def create_project(req: ProjectCreate, _user: str = Depends(require_user)) -> Project:
    return get_project_store().create_project(req.name, req.description)  # type: ignore[return-value]


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    project = get_project_store().get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"No project {project_id!r}")
    return project  # type: ignore[return-value]


@router.delete("/{project_id}")
def delete_project(project_id: str, _user: str = Depends(require_user)) -> dict[str, bool]:
    """Delete a project AND hard-delete its entire workspace subtree (irreversible)."""
    if project_id == DEFAULT_PROJECT:
        raise HTTPException(status_code=400, detail="The Default Workspace cannot be deleted.")
    if not get_project_store().delete_project(project_id):
        raise HTTPException(status_code=404, detail=f"No project {project_id!r}")
    return {"ok": True}
