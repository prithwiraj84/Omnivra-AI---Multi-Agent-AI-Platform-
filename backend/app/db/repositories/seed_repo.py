"""Seed-backed repository — the default, zero-dependency data source.

Builds the dashboard payload once from :func:`app.data.seed.build_dashboard`,
caches it on the instance, and slices it for the sub-resource methods. This is
what the app serves with no Supabase configuration, and what
:class:`~app.db.repositories.supabase_repo.SupabaseRepository` composes for the
data it does not yet read live from the database.
"""
from __future__ import annotations

from app.data.seed import build_dashboard
from app.schemas.dashboard import (
    Agent,
    ActivityItem,
    ApprovalItem,
    DashboardPayload,
    HealthMetric,
    WorkflowItem,
)


class SeedRepository:
    """In-memory repository over the static seed dashboard."""

    def __init__(self) -> None:
        self._payload: DashboardPayload = build_dashboard()

    def get_dashboard(self) -> DashboardPayload:
        return self._payload

    def list_agents(self) -> list[Agent]:
        # All 23: primary agents followed by system-ops agents.
        return [*self._payload.agents, *self._payload.system_ops]

    def get_agent(self, agent_id: str) -> Agent | None:
        for agent in self.list_agents():
            if agent.id == agent_id:
                return agent
        return None

    def list_workflows(self) -> list[WorkflowItem]:
        return self._payload.workflows

    def list_approvals(self) -> list[ApprovalItem]:
        return self._payload.approvals

    def list_activity(self) -> list[ActivityItem]:
        return self._payload.activity

    def get_system_health(self) -> list[HealthMetric]:
        return self._payload.system_health
