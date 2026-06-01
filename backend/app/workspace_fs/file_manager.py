"""Workspace file manager - enforces the sandbox rule.

AI agents may ONLY create/modify artifacts under the workspace root
(workspace/frontend, workspace/backend, workspace/docs, workspace/presentations,
workspace/reports). Every write goes through :class:`FileManager`, which resolves
the target and rejects any path that escapes the sandbox (path traversal),
guaranteeing agents can never touch project source code.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.core.logging import logger

SUBDIRS = ("frontend", "backend", "docs", "presentations", "reports")
STATE_DIR = ".state"
CHECKPOINT_DIR = ".checkpoints"


class WorkspaceViolationError(Exception):
    """Raised when a write would escape the workspace sandbox."""


@dataclass(slots=True)
class ManifestEntry:
    rel_path: str
    size_bytes: int
    written_at: str
    agent_id: str | None = None


class FileManager:
    """Sandboxed file operations rooted at the workspace directory."""

    def __init__(self, workspace_root: str | Path) -> None:
        self.root = Path(workspace_root).resolve()

    def ensure_layout(self) -> None:
        """Create the workspace root and standard subdirectories if missing."""
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in (*SUBDIRS, STATE_DIR, CHECKPOINT_DIR):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    def _resolve(self, rel_path: str | Path) -> Path:
        """Resolve a workspace-relative path, rejecting traversal outside root."""
        candidate = (self.root / Path(rel_path)).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise WorkspaceViolationError(
                f"Path {rel_path!r} escapes the workspace sandbox"
            )
        return candidate

    def write_text(
        self, rel_path: str | Path, content: str, *, agent_id: str | None = None
    ) -> ManifestEntry:
        """Write a UTF-8 text artifact inside the sandbox; return its manifest entry."""
        target = self._resolve(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info("Artifact written: {} (agent={})", rel_path, agent_id)
        return ManifestEntry(
            rel_path=str(Path(rel_path)),
            size_bytes=len(content.encode("utf-8")),
            written_at=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
        )

    def write_bytes(
        self, rel_path: str | Path, data: bytes, *, agent_id: str | None = None
    ) -> ManifestEntry:
        """Write a binary artifact (e.g. generated image) inside the sandbox."""
        target = self._resolve(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        logger.info("Binary artifact written: {} (agent={})", rel_path, agent_id)
        return ManifestEntry(
            rel_path=str(Path(rel_path)),
            size_bytes=len(data),
            written_at=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
        )

    def read_text(self, rel_path: str | Path) -> str:
        return self._resolve(rel_path).read_text(encoding="utf-8")

    def media_file(self, rel_path: str | Path) -> Path:
        """Resolve a path-jailed artifact for serving (e.g. a rendered .mp4 / image).

        Returns the absolute path (raising WorkspaceViolationError if it escapes the
        sandbox, FileNotFoundError if it isn't a real file) for a streaming response.
        """
        target = self._resolve(rel_path)
        if not target.is_file():
            raise FileNotFoundError(str(rel_path))
        return target

    def exists(self, rel_path: str | Path) -> bool:
        return self._resolve(rel_path).exists()

    def delete_path(self, rel_path: str | Path) -> bool:
        """Delete a file OR directory tree inside the sandbox (path-jailed).

        Returns True if something was removed. Refuses to delete the workspace root
        itself. Used to purge a social draft's artifacts on delete.
        """
        target = self._resolve(rel_path)
        if target == self.root:
            raise WorkspaceViolationError("refusing to delete the workspace root")
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
            return True
        if target.is_file():
            target.unlink(missing_ok=True)
            return True
        return False
