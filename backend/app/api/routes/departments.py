"""Department command-center routes (cp-0048).

GET /api/departments               -> the list of department slugs + titles.
GET /api/departments/{slug}/overview -> the full per-department command-center payload.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.departments import DepartmentOverview
from app.services.departments import DEPARTMENTS, build_department_overview

router = APIRouter(tags=["departments"])


@router.get("")
def list_departments() -> list[dict[str, str]]:
    """The department slugs + display titles (for nav / discovery)."""
    return [{"slug": slug, "title": title} for slug, (title, _vals, _note) in DEPARTMENTS.items()]


@router.get("/{slug}/overview", response_model=DepartmentOverview)
def department_overview(slug: str) -> DepartmentOverview:
    """Aggregated command-center data for one department (agents, KPIs, tasks, runs, outputs)."""
    overview = build_department_overview(slug)
    if overview is None:
        raise HTTPException(status_code=404, detail=f"Unknown department {slug!r}")
    return overview
