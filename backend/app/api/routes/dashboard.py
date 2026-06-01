"""Dashboard route: the single aggregate payload the frontend renders.

``GET /api/dashboard`` returns the whole :class:`DashboardPayload` (stats, agents,
workflows, charts, activity, approvals, health, usage, achievements) in one call.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app import schemas
from app.api.deps import get_repo
from app.db.repositories import DashboardRepository
from app.services.dashboard_live import build_live_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("", response_model=schemas.DashboardPayload)
def get_dashboard(repo: DashboardRepository = Depends(get_repo)) -> schemas.DashboardPayload:
    """Full aggregate dashboard payload (camelCase). Agents come from the repo
    (registry/Supabase); operational fields are computed live from the running
    system (workflow runs, tasks, RAG sizes, approvals, usage) — not seed demo."""
    return build_live_dashboard(repo.get_dashboard())
