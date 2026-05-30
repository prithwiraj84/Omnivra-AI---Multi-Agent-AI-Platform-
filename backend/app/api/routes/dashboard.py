"""Dashboard route: the single aggregate payload the frontend renders.

``GET /api/dashboard`` returns the whole :class:`DashboardPayload` (stats, agents,
workflows, charts, activity, approvals, health, usage, achievements) in one call.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app import schemas
from app.api.deps import get_repo
from app.db.repositories import DashboardRepository

router = APIRouter(tags=["dashboard"])


@router.get("", response_model=schemas.DashboardPayload)
def get_dashboard(repo: DashboardRepository = Depends(get_repo)) -> schemas.DashboardPayload:
    """Return the full aggregate dashboard payload (camelCase JSON)."""
    return repo.get_dashboard()
