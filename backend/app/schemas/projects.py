"""Projects + Tasks API schemas. camelCase on the wire."""
from __future__ import annotations

from app.schemas.dashboard import CamelModel


class Project(CamelModel):
    id: str
    name: str
    description: str = ""
    status: str = "active"  # active | paused | archived
    created_at: str
    task_count: int = 0


class ProjectCreate(CamelModel):
    name: str
    description: str = ""


class Task(CamelModel):
    id: str
    title: str
    project_id: str | None = None
    status: str = "todo"  # todo | in_progress | review | done
    priority: str = "medium"  # high | medium | low
    agent_id: str | None = None
    created_at: str


class TaskCreate(CamelModel):
    title: str
    project_id: str | None = None
    priority: str = "medium"
    agent_id: str | None = None


class TaskUpdate(CamelModel):
    title: str | None = None
    status: str | None = None
    priority: str | None = None
