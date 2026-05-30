"""Project state, file manifest, and checkpoint persistence.

This is the resume backbone: a workflow's ProjectState (status + manifest +
ordered checkpoint list) is serialised to JSON under workspace/.state, and each
checkpoint snapshot under workspace/.checkpoints. If a run is interrupted, the
Recovery Agent loads the latest checkpoint and resumes.

Phase 1: local filesystem JSON (works offline, zero infra).
Phase 3: durable LangGraph checkpoints in Supabase Postgres via
langgraph-checkpoint-postgres; this store keeps the human-facing manifest/state.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.logging import logger
from app.workspace_fs.file_manager import CHECKPOINT_DIR, STATE_DIR, ManifestEntry


class Checkpoint(BaseModel):
    checkpoint_id: str = Field(default_factory=lambda: f"ckpt_{uuid4().hex[:12]}")
    label: str
    recursion_count: int = 0
    state_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectState(BaseModel):
    workflow_id: str
    project_id: str
    status: str = "pending"
    manifest: list[dict[str, Any]] = Field(default_factory=list)
    checkpoints: list[Checkpoint] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckpointStore:
    """Filesystem-backed state + checkpoint persistence under the workspace."""

    def __init__(self, workspace_root: str | Path) -> None:
        self._root = Path(workspace_root).resolve()
        self._state_dir = self._root / STATE_DIR
        self._ckpt_dir = self._root / CHECKPOINT_DIR
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._ckpt_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_id(workflow_id: str) -> str:
        """Reject any workflow_id that could escape the state/checkpoint dir (defense-in-depth)."""
        if not workflow_id or any(c in workflow_id for c in ("/", "\\", "\x00")) or ".." in workflow_id:
            raise ValueError(f"Invalid workflow_id: {workflow_id!r}")
        return workflow_id

    def _state_file(self, workflow_id: str) -> Path:
        return self._state_dir / f"{self._safe_id(workflow_id)}.json"

    def load(self, workflow_id: str) -> ProjectState | None:
        path = self._state_file(workflow_id)
        if not path.exists():
            return None
        return ProjectState.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, state: ProjectState) -> None:
        state.updated_at = datetime.now(timezone.utc)
        self._state_file(state.workflow_id).write_text(
            state.model_dump_json(indent=2), encoding="utf-8"
        )

    def add_manifest_entry(self, workflow_id: str, entry: ManifestEntry) -> ProjectState:
        state = self.load(workflow_id) or ProjectState(
            workflow_id=workflow_id, project_id=workflow_id
        )
        state.manifest.append(
            {
                "rel_path": entry.rel_path,
                "size_bytes": entry.size_bytes,
                "written_at": entry.written_at,
                "agent_id": entry.agent_id,
            }
        )
        self.save(state)
        return state

    def checkpoint(
        self, workflow_id: str, *, label: str, state_snapshot: dict[str, Any]
    ) -> Checkpoint:
        """Append a checkpoint to project state and write its snapshot file."""
        ckpt = Checkpoint(
            label=label,
            recursion_count=int(state_snapshot.get("recursion_count", 0)),
            state_snapshot=state_snapshot,
        )
        state = self.load(workflow_id) or ProjectState(
            workflow_id=workflow_id, project_id=workflow_id
        )
        state.checkpoints.append(ckpt)
        self.save(state)
        (self._ckpt_dir / f"{self._safe_id(workflow_id)}__{ckpt.checkpoint_id}.json").write_text(
            json.dumps(json.loads(ckpt.model_dump_json()), indent=2), encoding="utf-8"
        )
        logger.info("Checkpoint {} ({}) saved for {}", ckpt.checkpoint_id, label, workflow_id)
        return ckpt

    def latest_checkpoint(self, workflow_id: str) -> Checkpoint | None:
        """Return the most recent checkpoint for resume (Recovery Agent entrypoint)."""
        state = self.load(workflow_id)
        if not state or not state.checkpoints:
            return None
        return state.checkpoints[-1]
