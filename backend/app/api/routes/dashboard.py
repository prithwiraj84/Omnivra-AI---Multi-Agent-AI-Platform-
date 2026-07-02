"""Dashboard route: the single aggregate payload the frontend renders.

``GET /api/dashboard`` returns the whole :class:`DashboardPayload` (stats, agents,
workflows, charts, activity, approvals, health, usage, achievements) in one call.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app import schemas
from app.api.deps import current_user, get_repo
from app.core.config import get_settings
from app.db.repositories import DashboardRepository
from app.services.dashboard_live import build_live_dashboard

router = APIRouter(tags=["dashboard"])

# Short-TTL cache, keyed PER USER: build_live_dashboard scans the user's projects per call and the
# SPA polls every few seconds, so a 1-2s cache collapses many rebuilds into one with negligible
# staleness. Keyed by owner so one user's payload is never served to another. DASHBOARD_CACHE_TTL=0
# disables it.
_cache: dict[str, dict] = {}


@router.get("", response_model=schemas.DashboardPayload)
def get_dashboard(
    repo: DashboardRepository = Depends(get_repo),
    current: str = Depends(current_user),
) -> schemas.DashboardPayload:
    """Full aggregate dashboard payload (camelCase), scoped to the current user. Agents come
    from the repo (registry/Supabase); operational fields are computed live from the user's
    running system (their workflow runs, tasks, RAG sizes, approvals, usage) — not seed demo."""
    ttl = get_settings().dashboard_cache_ttl
    now = time.monotonic()
    entry = _cache.get(current)
    if ttl > 0 and entry is not None and (now - entry["ts"]) < ttl:
        return entry["payload"]
    payload = build_live_dashboard(repo.get_dashboard(), owner_id=current)
    _cache[current] = {"ts": now, "payload": payload}
    return payload
