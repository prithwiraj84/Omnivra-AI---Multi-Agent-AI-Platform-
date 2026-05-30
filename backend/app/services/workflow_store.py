"""WorkflowStore — durable run metadata under workspace/.state/workflows/.

Persists each workflow run (RunResult) so runs can be listed, inspected, and the
awaiting-approval ones surfaced for recovery. The live interrupt/resume itself uses
the LangGraph in-memory checkpointer (same-process); this store is the queryable,
restart-surviving record. A Postgres checkpointer (Supabase) would make resume
durable across restarts too — see docs/SUPABASE_INTEGRATION.md.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import logger
from app.schemas.orchestration import RunResult


class WorkflowStore:
    def __init__(self, root: Path) -> None:
        self._dir = Path(root) / ".state" / "workflows"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, workflow_id: str) -> Path:
        if not workflow_id or any(c in workflow_id for c in ("/", "\\", "\x00")) or ".." in workflow_id:
            raise ValueError(f"Invalid workflow_id: {workflow_id!r}")
        return self._dir / f"{workflow_id}.json"

    def save(self, run: RunResult) -> None:
        self._path(run.workflow_id).write_text(run.model_dump_json(by_alias=True, indent=2), encoding="utf-8")

    def get(self, workflow_id: str) -> RunResult | None:
        try:
            path = self._path(workflow_id)
        except ValueError:
            return None
        if not path.exists():
            return None
        try:
            return RunResult.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - tolerate a corrupt record
            logger.warning("Could not read workflow record {}: {}", workflow_id, exc)
            return None

    def list(self, *, status: str | None = None) -> list[RunResult]:
        runs: list[RunResult] = []
        for path in self._dir.glob("*.json"):
            run = self.get(path.stem)
            if run and (status is None or run.status == status):
                runs.append(run)
        return runs

    def find_by_approval(self, approval_id: str) -> RunResult | None:
        for run in self.list():
            if run.pending_approval and run.pending_approval.approval_id == approval_id:
                return run
        return None


@lru_cache(maxsize=1)
def get_workflow_store() -> WorkflowStore:
    return WorkflowStore(get_settings().workspace_path)
