"""Department command-center DTOs (cp-0048). camelCase on the wire.

A single GET /api/departments/{slug}/overview aggregates everything a department page
needs: its agents (with live status + per-agent usage), KPI stat cards, the tasks /
workflow runs / artifacts that flow through the department, a recent activity feed,
provider usage, and a short execution trend. Mirrors the frontend DTO types.
"""
from __future__ import annotations

from app.schemas.dashboard import CamelModel, StatCard, TaskPoint


class DeptAgent(CamelModel):
    id: str
    name: str
    status: str  # working | needs_approval | idle
    provider: str
    model: str
    model_label: str
    accent: str
    kind: str
    calls: int  # times this agent produced output across all runs
    last_activity: str | None  # ISO time of its most recent artifact, or None
    responsibilities: list[str]


class DeptTask(CamelModel):
    id: str
    title: str
    status: str  # todo | in_progress | review | done
    priority: str


class DeptWorkflow(CamelModel):
    id: str
    task: str
    status: str
    agents: int  # how many of this department's agents took part


class DeptOutput(CamelModel):
    path: str
    category: str
    size_bytes: int
    modified: str
    agent_id: str | None
    project_id: str  # needed to build the /workspace/media download URL (artifacts span projects)


class DeptActivity(CamelModel):
    id: str
    agent: str
    action: str
    time: str
    accent: str
    icon: str


class ProviderCalls(CamelModel):
    provider: str
    label: str
    calls: int


class DepartmentOverview(CamelModel):
    slug: str
    title: str
    note: str
    accent: str
    stats: list[StatCard] = []
    agents: list[DeptAgent] = []
    tasks: list[DeptTask] = []
    workflows: list[DeptWorkflow] = []
    activity: list[DeptActivity] = []
    outputs: list[DeptOutput] = []
    provider_usage: list[ProviderCalls] = []
    execution: list[TaskPoint] = []
