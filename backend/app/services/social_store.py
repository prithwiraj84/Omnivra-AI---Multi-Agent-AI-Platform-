"""SocialDraftStore — per-project social content drafts under .state/social/.

Mirrors WorkflowStore: JSON-backed, project-keyed factory, path-jailed ids. Each
draft is a SocialDraft (reel or post) with its approval status + publish results.
"""
from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path

from app.core.logging import logger
from app.schemas.social import SocialDraft
from app.workspace_fs.paths import DEFAULT_PROJECT, project_root


class SocialDraftStore:
    def __init__(self, root: Path) -> None:
        self._dir = Path(root) / ".state" / "social"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()  # guard JSON I/O (sync routes run in a threadpool)

    def _path(self, draft_id: str) -> Path:
        if not draft_id or any(c in draft_id for c in ("/", "\\", "\x00")) or ".." in draft_id:
            raise ValueError(f"Invalid draft_id: {draft_id!r}")
        return self._dir / f"{draft_id}.json"

    def save(self, draft: SocialDraft) -> None:
        with self._lock:
            self._path(draft.id).write_text(draft.model_dump_json(by_alias=True, indent=2), encoding="utf-8")

    def get(self, draft_id: str) -> SocialDraft | None:
        try:
            path = self._path(draft_id)
        except ValueError:
            return None
        with self._lock:
            if not path.exists():
                return None
            try:
                return SocialDraft.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001 - tolerate a corrupt record
                logger.warning("Could not read social draft {}: {}", draft_id, exc)
                return None

    def list(self) -> list[SocialDraft]:
        with self._lock:
            stems = [p.stem for p in self._dir.glob("*.json")]  # snapshot the listing under the lock
        drafts = [d for stem in stems if (d := self.get(stem))]
        drafts.sort(key=lambda d: d.created_at, reverse=True)  # newest first
        return drafts


@lru_cache(maxsize=None)
def get_social_store(project_id: str = DEFAULT_PROJECT) -> SocialDraftStore:
    """Per-project social draft store (workspace/projects/<project_id>/.state/social/)."""
    return SocialDraftStore(project_root(project_id))
