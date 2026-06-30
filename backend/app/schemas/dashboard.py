"""Dashboard API DTOs.

Serialized camelCase (via ``to_camel`` alias generator) so the JSON matches the
frontend TypeScript DTO types in ``frontend/src/lib/api/types.ts`` field-for-field.
``icon`` fields carry a string key resolved to a Lucide icon on the client
(see ``frontend/src/lib/api/icons.ts``). ``accent`` is one of the design accents
(cyan|violet|blue|emerald|amber|pink).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model: snake_case in Python, camelCase on the wire."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class StatCard(CamelModel):
    label: str
    value: str
    sub: str | None = None
    delta: str | None = None
    delta_tone: str | None = None
    accent: str
    icon: str


class Agent(CamelModel):
    id: str
    name: str
    department: str
    accent: str
    provider: str
    provider_label: str
    model: str
    model_label: str
    kind: str
    status: str


class WorkflowItem(CamelModel):
    id: str
    name: str
    department: str
    status: str  # In Progress | Review | Completed | Failed | Queued
    progress: int
    accent: str
    icon: str
    current_agent: str | None = None  # the agent working RIGHT NOW (live, while In Progress)


class TaskPoint(CamelModel):
    time: str
    completed: int
    in_progress: int
    failed: int


class SeriesDef(CamelModel):
    key: str
    label: str
    color: str


class DistributionSlice(CamelModel):
    name: str
    value: int
    color: str


class ActivityItem(CamelModel):
    id: str
    agent: str
    action: str
    time: str
    accent: str
    icon: str


class ApprovalItem(CamelModel):
    id: str
    title: str
    source: str
    priority: str  # high | medium | low
    icon: str
    accent: str


class HealthMetric(CamelModel):
    label: str
    pct: int | None = None  # null => non-numeric status (e.g. Network = "Good")
    display: str
    accent: str


class ProviderUsage(CamelModel):
    name: str
    pct: int
    calls: int
    color: str


class ModelUsage(CamelModel):
    id: str
    pct: int
    calls: int
    color: str


class MediaService(CamelModel):
    name: str
    provider: str
    calls: int
    delta: str
    accent: str
    icon: str


class Achievement(CamelModel):
    title: str
    subtitle: str
    icon: str
    accent: str


class DashboardPayload(CamelModel):
    """Everything the dashboard needs in one response (GET /api/dashboard)."""

    stats: list[StatCard]
    agents: list[Agent]
    system_ops: list[Agent]
    workflows: list[WorkflowItem]
    task_execution: list[TaskPoint]
    task_execution_series: list[SeriesDef]
    task_distribution: list[DistributionSlice]
    total_tasks: int
    activity: list[ActivityItem]
    approvals: list[ApprovalItem]
    total_pending_approvals: int
    system_health: list[HealthMetric]
    provider_usage: list[ProviderUsage]
    model_usage: list[ModelUsage]
    media_services: list[MediaService]
    achievements: list[Achievement]
