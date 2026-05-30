"""Activity routes: list the recent activity feed."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app import schemas
from app.api.deps import get_repo
from app.db.repositories import DashboardRepository

router = APIRouter(tags=["activity"])


@router.get("", response_model=list[schemas.ActivityItem])
def list_activity(repo: DashboardRepository = Depends(get_repo)) -> list[schemas.ActivityItem]:
    """Return the recent activity feed."""
    return repo.list_activity()
