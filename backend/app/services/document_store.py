"""DocumentStore — per-project Document Studio drafts under .state/documents/.

Mirrors SocialDraftStore: JSON-backed, project-keyed factory, path-jailed ids,
thread-safe (sync routes run in a threadpool).
"""
from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path

from app.core.logging import logger
from app.schemas.documents import DocumentDraft
from app.workspace_fs.paths import DEFAULT_PROJECT, project_root


class DocumentStore:
    def __init__(self, root: Path) -> None:
        self._dir = Path(root) / ".state" / "documents"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, doc_id: str) -> Path:
        if not doc_id or any(c in doc_id for c in ("/", "\\", "\x00")) or ".." in doc_id:
            raise ValueError(f"Invalid doc_id: {doc_id!r}")
        return self._dir / f"{doc_id}.json"

    def save(self, draft: DocumentDraft) -> None:
        with self._lock:
            self._path(draft.id).write_text(draft.model_dump_json(by_alias=True, indent=2), encoding="utf-8")

    def get(self, doc_id: str) -> DocumentDraft | None:
        try:
            path = self._path(doc_id)
        except ValueError:
            return None
        with self._lock:
            if not path.exists():
                return None
            try:
                return DocumentDraft.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001 - tolerate a corrupt record
                logger.warning("Could not read document draft {}: {}", doc_id, exc)
                return None

    def list(self) -> list[DocumentDraft]:
        with self._lock:
            stems = [p.stem for p in self._dir.glob("*.json")]
        drafts = [d for stem in stems if (d := self.get(stem))]
        drafts.sort(key=lambda d: d.created_at, reverse=True)
        return drafts


@lru_cache(maxsize=None)
def get_document_store(project_id: str = DEFAULT_PROJECT) -> DocumentStore:
    """Per-project document store (workspace/projects/<project_id>/.state/documents/)."""
    return DocumentStore(project_root(project_id))
