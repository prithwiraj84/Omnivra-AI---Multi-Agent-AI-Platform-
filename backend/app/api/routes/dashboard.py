"""Dashboard route: the single aggregate payload the frontend renders.

``GET /api/dashboard`` returns the whole :class:`DashboardPayload` (stats, agents,
workflows, charts, activity, approvals, health, usage, achievements) in one call.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app import schemas
from app.api.deps import get_repo
from app.core.config import get_settings
from app.db.repositories import DashboardRepository
from app.services.dashboard_live import build_live_dashboard

router = APIRouter(tags=["dashboard"])

# Process-wide short-TTL cache: build_live_dashboard scans EVERY project per call, and the SPA polls
# this route every few seconds across clients, so a 1-2s cache collapses many rebuilds into one with
# negligible staleness (live agent status lags at most the TTL). Disabled when DASHBOARD_CACHE_TTL=0.
_cache: dict = {"ts": 0.0, "payload": None}


@router.get("", response_model=schemas.DashboardPayload)
def get_dashboard(repo: DashboardRepository = Depends(get_repo)) -> schemas.DashboardPayload:
    """Full aggregate dashboard payload (camelCase). Agents come from the repo
    (registry/Supabase); operational fields are computed live from the running
    system (workflow runs, tasks, RAG sizes, approvals, usage) — not seed demo."""
    ttl = get_settings().dashboard_cache_ttl
    now = time.monotonic()
    if ttl > 0 and _cache["payload"] is not None and (now - _cache["ts"]) < ttl:
        return _cache["payload"]
    payload = build_live_dashboard(repo.get_dashboard())
    _cache["ts"], _cache["payload"] = now, payload
    return payload
