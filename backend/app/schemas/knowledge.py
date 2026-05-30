"""Knowledge Base + Memory API schemas. camelCase on the wire."""
from __future__ import annotations

from typing import Any

from app.schemas.dashboard import CamelModel


class KnowledgeAddRequest(CamelModel):
    text: str
    source: str | None = "manual"
    metadata: dict[str, Any] = {}


class AddResult(CamelModel):
    id: str


class SearchResult(CamelModel):
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = {}


class IngestResult(CamelModel):
    ingested: int
    total: int


class StoreStats(CamelModel):
    count: int


class MemoryItem(CamelModel):
    id: str
    text: str
    metadata: dict[str, Any] = {}
