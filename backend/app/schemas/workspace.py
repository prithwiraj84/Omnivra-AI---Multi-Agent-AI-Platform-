"""Workspace artifact schemas. camelCase on the wire."""
from __future__ import annotations

from app.schemas.dashboard import CamelModel


class Artifact(CamelModel):
    path: str
    category: str
    size_bytes: int
    modified: str
    agent_id: str | None = None


class ArtifactContent(CamelModel):
    path: str
    content: str


class RunProgramRequest(CamelModel):
    """Run one workspace file (path-jailed) — POST /api/workspace/run."""

    path: str


class RunProgramResult(CamelModel):
    """Captured outcome of a guarded in-workspace run. camelCase on the wire."""

    path: str
    command: str
    ok: bool
    exit_code: int | None = None
    timed_out: bool = False
    duration_ms: int = 0
    stdout: str = ""
    stderr: str = ""
    note: str = ""
