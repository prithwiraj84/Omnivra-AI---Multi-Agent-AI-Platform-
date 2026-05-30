"""Local vector store + embedder — the offline-capable foundation for KB + memory.

`embed()` is a deterministic hashing embedder (no network, no API key): tokens are
hashed into a fixed-dim, L2-normalized vector, so cosine similarity gives usable
semantic-ish retrieval offline. A VectorStore is an in-memory cosine index persisted
to workspace/.state/vectors/<name>.json. When Supabase is configured, the same
KnowledgeService/MemoryService interface can be backed by pgvector + match_* RPCs
(see docs/SUPABASE_INTEGRATION.md) — this local store is the zero-config default.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

EMBED_DIM = 256
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def embed(text: str) -> list[float]:
    """Deterministic hashing embedding (signed hashing trick), L2-normalized."""
    vec = [0.0] * EMBED_DIM
    for tok in _TOKEN_RE.findall((text or "").lower()):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % EMBED_DIM] += 1.0 if (h >> 8) & 1 else -1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity for already-normalized vectors (= dot product)."""
    return sum(x * y for x, y in zip(a, b))


class VectorStore:
    """An in-memory cosine index persisted to JSON. Items: {id, text, metadata, embedding}."""

    def __init__(self, name: str, root: str | Path) -> None:
        self.name = name
        self._path = Path(root) / ".state" / "vectors" / f"{name}.json"
        self._items: list[dict[str, Any]] = []
        self._lock = threading.RLock()  # guard read-modify-write (sync routes run in a threadpool)
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._items = json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001 - tolerate a corrupt index
                self._items = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._items), encoding="utf-8")

    def add(self, text: str, metadata: dict[str, Any] | None = None, *, id: str | None = None) -> str:
        item_id = id or uuid4().hex
        record = {"id": item_id, "text": text, "metadata": metadata or {}, "embedding": embed(text)}
        with self._lock:
            for i, existing in enumerate(self._items):
                if existing["id"] == item_id:  # upsert by id (idempotent ingest)
                    self._items[i] = record
                    break
            else:
                self._items.append(record)
            self._save()
        return item_id

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        if not self._items:
            return []
        qe = embed(query)
        scored = [
            {"id": it["id"], "text": it["text"], "metadata": it.get("metadata", {}), "score": round(cosine(qe, it["embedding"]), 4)}
            for it in self._items
        ]
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:k]

    def recent(self, n: int = 20) -> list[dict[str, Any]]:
        return [
            {"id": it["id"], "text": it["text"], "metadata": it.get("metadata", {})}
            for it in reversed(self._items[-n:])
        ]

    @property
    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items = []
            self._save()
