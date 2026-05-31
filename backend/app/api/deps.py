"""FastAPI dependencies for the REST API.

``get_repo`` resolves the process-wide dashboard repository (Supabase when configured,
else seed). ``require_user`` is the auth gate: a no-op returning the admin user when
``auth_enabled`` is False (dev/open mode), and a Bearer-token check when enabled.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, Query

from app.core.config import get_settings
from app.core.security import verify_token
from app.db.repositories import DashboardRepository, get_repository
from app.services.project_store import get_project_store
from app.workspace_fs.paths import DEFAULT_PROJECT, safe_project_id


def get_repo() -> DashboardRepository:
    """Return the active dashboard repository."""
    return get_repository()


def get_project_id(
    x_project_id: str | None = Header(default=None),
    projectId: str | None = Query(default=None),
) -> str:
    """Resolve the active project for a request: X-Project-Id header or ?projectId= query.

    Defaults to the Default Workspace, rejects ids that could escape the projects/
    directory (per-project path jail) with a 400, and rejects unknown/deleted projects
    with a 404 — so a stale or crafted id can never silently recreate a purged subtree.
    """
    try:
        pid = safe_project_id(x_project_id or projectId)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if pid != DEFAULT_PROJECT and get_project_store().get_project(pid) is None:
        raise HTTPException(status_code=404, detail=f"No project {pid!r}")
    return pid


def require_user(authorization: str | None = Header(default=None)) -> str:
    """Auth gate. Open (returns admin) unless settings.auth_enabled; else require a valid Bearer token."""
    settings = get_settings()
    if not settings.auth_enabled:
        return settings.admin_username
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = verify_token(authorization.split(" ", 1)[1].strip())
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
