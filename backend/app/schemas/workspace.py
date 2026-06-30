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


# --- Universal app runner (cp-0054) ----------------------------------------
class AppRunRequest(CamelModel):
    """Run a whole generated project dir (e.g. "docs/wf_xxx") — POST /api/workspace/app/run."""

    dir: str


class AppStopRequest(CamelModel):
    """Stop a running project (by dir) or a single target (by runKey)."""

    dir: str | None = None
    run_key: str | None = None


class AppTarget(CamelModel):
    """One runnable target (a backend or frontend) and its live process state. camelCase on the wire."""

    run_key: str
    rel: str
    kind: str                      # python | node
    name: str
    framework: str = ""
    status: str = "idle"           # idle|installing|starting|running|exited|error|stopped
    port: int | None = None
    url: str | None = None
    exit_code: int | None = None
    note: str = ""
    logs_tail: str = ""


class AppRunStatus(CamelModel):
    """Aggregate run status for a generated project directory."""

    dir: str
    targets: list[AppTarget] = []
    note: str = ""


class AppInfo(CamelModel):
    """One generated app (workflow), de-duplicated across category dirs to its best root."""

    wf_id: str
    dir: str
    name: str
