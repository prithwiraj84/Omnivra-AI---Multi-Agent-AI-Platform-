"""KnowledgeService — the searchable Knowledge Base (RAG corpus).

Backed by the local VectorStore by default. Ingests workspace artifacts and arbitrary
text; agents/UI search it. (Swap to Supabase pgvector when configured.)
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.logging import logger
from app.services.artifacts import get_artifact_service
from app.services.vectorstore import VectorStore


class KnowledgeService:
    def __init__(self, root: str) -> None:
        self._store = VectorStore("knowledge", root)

    def add_text(self, text: str, source: str = "manual", metadata: dict[str, Any] | None = None, *, id: str | None = None) -> str:
        meta = {"source": source, **(metadata or {})}
        return self._store.add(text, meta, id=id)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        return self._store.search(query, k=k)

    def ingest_workspace(self) -> int:
        """Index every workspace artifact into the KB (idempotent by path). Returns count ingested."""
        svc = get_artifact_service()
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


@lru_cache(maxsize=1)
def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService(str(get_settings().workspace_path))
