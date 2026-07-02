"""FastAPI dependencies for the REST API.

``get_repo`` resolves the process-wide dashboard repository (Supabase when configured,
else seed). ``current_user`` is the identity that OWNS a request's data (per-user isolation);
``require_user`` is the older auth gate kept for endpoints that only need "is authenticated".
"""
from __future__ import annotations

import jwt
from fastapi import Depends, Header, HTTPException, Query

from app.core.config import get_settings
from app.core.security import verify_token
from app.db.repositories import DashboardRepository, get_repository
from app.services.project_store import get_project_store
from app.workspace_fs.paths import DEFAULT_PROJECT, safe_project_id


def get_repo() -> DashboardRepository:
    """Return the active dashboard repository."""
    return get_repository()


def _bearer(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def current_user(authorization: str | None = Header(default=None)) -> str:
    """The identity that owns this request's projects/workspace.

    - PER-USER mode (SUPABASE_JWT_SECRET set): verify the request's Supabase access token
      (HS256, aud=authenticated) and return its user id (`sub`). No/invalid token -> 401.
    - Single-admin/open mode (secret unset): always the admin username, so every existing
      test + local run behaves exactly as before (one owner, no auth required).
    """
    settings = get_settings()
    secret = settings.supabase_jwt_secret
    if not secret:
        return settings.admin_username
    token = _bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    except Exception as exc:  # noqa: BLE001 - any JWT error is an auth failure
        raise HTTPException(status_code=401, detail="Invalid or expired session") from exc
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid session (no subject)")
    return str(sub)


def get_project_id(
    current: str = Depends(current_user),
    x_project_id: str | None = Header(default=None),
    projectId: str | None = Query(default=None),
) -> str:
    """Resolve the active project for a request, SCOPED TO THE CURRENT USER.

    An empty id — or the legacy shared "default" — maps to *this user's* Default Workspace
    (created on first use). Any other id must be owned by the current user, else 404 (we return
    404 rather than 403 so a crafted/foreign id never reveals another user's project existence).
    Ids that could escape the projects/ path jail are rejected with 400.
    """
    raw = x_project_id or projectId
    store = get_project_store()
    if not raw or raw == DEFAULT_PROJECT:
        return store.ensure_user_default(current)
    try:
        pid = safe_project_id(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if store.get_project(pid, owner_id=current) is None:
        raise HTTPException(status_code=404, detail=f"No project {pid!r}")
    return pid


def require_user(authorization: str | None = Header(default=None)) -> str:
    """Auth gate. Open (returns admin) unless settings.auth_enabled; else require a valid Bearer token."""
    settings = get_settings()
    if not settings.auth_enabled:
        return settings.admin_username
    token = _bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
