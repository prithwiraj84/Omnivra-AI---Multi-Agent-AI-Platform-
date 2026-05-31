"""KnowledgeService — the searchable Knowledge Base (RAG corpus).

Backed by the local VectorStore by default. Ingests workspace artifacts and arbitrary
text; agents/UI search it. (Swap to Supabase pgvector when configured.)
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.logging import logger
from app.services.artifacts import get_artifact_service
from app.services.vectorstore import VectorStore
from app.workspace_fs.paths import DEFAULT_PROJECT, project_root


class KnowledgeService:
    def __init__(self, root: str, project_id: str = DEFAULT_PROJECT) -> None:
        self._store = VectorStore("knowledge", root)
        self._project_id = project_id

    def add_text(self, text: str, source: str = "manual", metadata: dict[str, Any] | None = None, *, id: str | None = None) -> str:
        meta = {"source": source, **(metadata or {})}
        return self._store.add(text, meta, id=id)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        return self._store.search(query, k=k)

    def ingest_workspace(self) -> int:
        """Index this project's workspace artifacts into its KB (idempotent by path). Returns count ingested."""
        svc = get_artifact_service(self._project_id)
        count = 0
        for art in svc.list_artifacts():
            path = art["path"]
            try:
                content = svc.read_artifact(path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("KB ingest skipped {}: {}", path, exc)
                continue
            if content.strip():
                self.add_text(content, source=path, metadata={"category": art.get("category"), "path": path}, id=f"art:{path}")
                count += 1
        logger.info("KB ingested {} workspace artifacts", count)
        return count

    @property
    def count(self) -> int:
        return self._store.count


@lru_cache(maxsize=None)
def get_knowledge_service(project_id: str = DEFAULT_PROJECT) -> KnowledgeService:
    """Per-project knowledge base (isolated RAG corpus per project)."""
    return KnowledgeService(str(project_root(project_id)), project_id)
