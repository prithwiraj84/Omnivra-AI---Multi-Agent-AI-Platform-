"""MemoryService — agent/workflow long-term memory (RAG over past work).

The orchestrator stores each agent output here after a run; the delegate node recalls
the most relevant memories for the current task and threads them into agent prompts,
so the company learns from its own prior work. Backed by the local VectorStore.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.services.vectorstore import VectorStore
from app.workspace_fs.paths import DEFAULT_PROJECT, project_root


class MemoryService:
    def __init__(self, root: str) -> None:
        self._store = VectorStore("memory", root)

    def remember(self, text: str, metadata: dict[str, Any] | None = None, *, id: str | None = None) -> str:
        return self._store.add(text, metadata or {}, id=id)

    def recall(self, query: str, k: int = 3, *, min_score: float = 0.05) -> list[dict[str, Any]]:
        """Top-k relevant memories above a small score floor (filters out noise)."""
        return [r for r in self._store.search(query, k=k) if r["score"] >= min_score]

    def recall_context(self, query: str, k: int = 3) -> str:
        """Recalled memories formatted as a context block for agent prompts ('' if none)."""
        hits = self.recall(query, k=k)
        if not hits:
            return ""
        lines = ["Relevant memory from earlier work:"]
        for h in hits:
            agent = (h.get("metadata") or {}).get("agent_id", "memory")
            snippet = h["text"][:280].strip()
            lines.append(f"- [{agent}] {snippet}")
        return "\n".join(lines)

    def recent(self, n: int = 20) -> list[dict[str, Any]]:
        return self._store.recent(n)

    @property
    def count(self) -> int:
        return self._store.count


@lru_cache(maxsize=None)
def get_memory_service(project_id: str = DEFAULT_PROJECT) -> MemoryService:
    """Per-project agent memory (RAG isolated per project — no cross-project recall)."""
    return MemoryService(str(project_root(project_id)))
