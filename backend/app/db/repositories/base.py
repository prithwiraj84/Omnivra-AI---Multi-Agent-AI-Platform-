"""Repository contract for the dashboard data layer.

:class:`DashboardRepository` is a structural ``typing.Protocol``: both
:class:`~app.db.repositories.seed_repo.SeedRepository` and
:class:`~app.db.repositories.supabase_repo.SupabaseRepository` satisfy it without
explicit inheritance. All methods are synchronous and return the camelCase DTOs
defined in :mod:`app.schemas.dashboard`.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.dashboard import (
    Agent,
    ActivityItem,
    ApprovalItem,
    DashboardPayload,
    HealthMetric,
    WorkflowItem,
)


@runtime_checkable
class DashboardRepository(Protocol):
    """Read interface backing the dashboard REST API."""

    def get_dashboard(self) -> DashboardPayload:
        """Return the full aggregate dashboard payload."""
        ...

    def list_agents(self) -> list[Agent]:
        """Return all agents (primary + system-ops), 23 total."""
        ...

    def get_agent(self, agent_id: str) -> Agent | None:
        """Return a single agent by id, or ``None`` when unknown."""
        ...

    def list_workflows(self) -> list[WorkflowItem]:
        """Return the active workflow items."""
        ...

    def list_approvals(self) -> list[ApprovalItem]:
        """Return pending approval items."""
        ...

    def list_activity(self) -> list[ActivityItem]:
        """Return the recent activity feed."""
        ...

    def get_system_health(self) -> list[HealthMetric]:
        """Return the system-health metrics."""
        ...
