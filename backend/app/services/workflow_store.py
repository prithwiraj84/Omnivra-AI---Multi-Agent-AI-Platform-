"""WorkflowStore — durable run metadata under workspace/.state/workflows/.

Persists each workflow run (RunResult) so runs can be listed, inspected, and the
awaiting-approval ones surfaced for recovery. The live interrupt/resume itself uses
the LangGraph in-memory checkpointer (same-process); this store is the queryable,
restart-surviving record. A Postgres checkpointer (Supabase) would make resume
durable across restarts too — see docs/SUPABASE_INTEGRATION.md.
"""
from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path

from app.core.logging import logger
from app.schemas.orchestration import RunResult
from app.workspace_fs.paths import DEFAULT_PROJECT, list_project_dir_ids, project_root


class WorkflowStore:
    def __init__(self, root: Path) -> None:
        self._dir = Path(root) / ".state" / "workflows"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()  # guard JSON I/O (sync routes run in a threadpool)

    def _path(self, workflow_id: str) -> Path:
        if not workflow_id or any(c in workflow_id for c in ("/", "\\", "\x00")) or ".." in workflow_id:
            raise ValueError(f"Invalid workflow_id: {workflow_id!r}")
        return self._dir / f"{workflow_id}.json"

    def save(self, run: RunResult) -> None:
        with self._lock:
            self._path(run.workflow_id).write_text(run.model_dump_json(by_alias=True, indent=2), encoding="utf-8")

    def get(self, workflow_id: str) -> RunResult | None:
        try:
            path = self._path(workflow_id)
        except ValueError:
            return None
        with self._lock:
            if not path.exists():
                return None
            try:
                return RunResult.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001 - tolerate a corrupt record
                logger.warning("Could not read workflow record {}: {}", workflow_id, exc)
                return None

    def list(self, *, status: str | None = None) -> list[RunResult]:
        with self._lock:
            paths = list(self._dir.glob("*.json"))  # snapshot the listing under the lock
        runs: list[RunResult] = []
        for path in paths:
            run = self.get(path.stem)
            if run and (status is None or run.status == status):
                runs.append(run)
        return runs

    def find_by_approval(self, approval_id: str) -> RunResult | None:
        for run in self.list():
            if run.pending_approval and run.pending_approval.approval_id == approval_id:
                return run
        return None


@lru_cache(maxsize=None)
def get_workflow_store(project_id: str = DEFAULT_PROJECT) -> WorkflowStore:
    """Per-project workflow run store (workspace/projects/<project_id>/.state/workflows/)."""
    return WorkflowStore(project_root(project_id))


def update_run_progress(
    project_id: str,
    workflow_id: str,
    *,
    current_agent: str | None = None,
    delegations: list[str] | None = None,
) -> None:
    """Best-effort LIVE progress update on a still-running run record, so the polled dashboard can
    show which agent is working RIGHT NOW (the graph nodes call this as they execute; the orchestrator
    overwrites the terminal record at the end). Never raises — progress telemetry must not break a run."""
    try:
        store = get_workflow_store(project_id)
        run = store.get(workflow_id)
        if run is None or run.status != "running":  # only annotate a live run
            return
        run.current_agent = current_agent
        if delegations is not None:
            run.delegations = delegations
        store.save(run)
    except Exception as exc:  # noqa: BLE001
        logger.debug("update_run_progress({}) skipped: {}", workflow_id, exc)


def find_run(workflow_id: str) -> tuple[str, RunResult] | None:
    """Locate a run across all projects by id. Returns (project_id, run) or None.

    Resume/approval flows only carry a workflow_id/approval_id, not the project, so
    we scan every project's store. Cheap for an offline single-admin OS.
    """
    for pid in list_project_dir_ids():
        run = get_workflow_store(pid).get(workflow_id)
        if run is not None:
            return pid, run
    return None


def find_by_approval(approval_id: str) -> tuple[str, RunResult] | None:
    """Locate the run awaiting a given approval_id across all projects."""
    for pid in list_project_dir_ids():
        run = get_workflow_store(pid).find_by_approval(approval_id)
        if run is not None:
            return pid, run
    return None
