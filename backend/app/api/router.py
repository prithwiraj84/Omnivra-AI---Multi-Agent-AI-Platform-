"""Top-level API router.

Aggregates every sub-router under its prefix. ``app.main`` includes this with
``prefix="/api"``, so the public paths are ``/api/dashboard``, ``/api/agents``,
``/api/workflows``, ``/api/approvals``, ``/api/activity``, ``/api/system/health``.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    activity,
    agents,
    approvals,
    auth,
    dashboard,
    knowledge,
    media,
    memory,
    projects,
    social,
    system,
    tasks,
    workflows,
    workspace,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(dashboard.router, prefix="/dashboard")
api_router.include_router(projects.router, prefix="/projects")
api_router.include_router(tasks.router, prefix="/tasks")
api_router.include_router(agents.router, prefix="/agents")
api_router.include_router(workflows.router, prefix="/workflows")
api_router.include_router(approvals.router, prefix="/approvals")
api_router.include_router(activity.router, prefix="/activity")
api_router.include_router(system.router, prefix="/system")
api_router.include_router(workspace.router, prefix="/workspace")
api_router.include_router(media.router, prefix="/media")
api_router.include_router(knowledge.router, prefix="/knowledge")
api_router.include_router(memory.router, prefix="/memory")
api_router.include_router(social.router, prefix="/social")
