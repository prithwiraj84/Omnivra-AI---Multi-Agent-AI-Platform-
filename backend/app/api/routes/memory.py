"""Memory routes: recall (search) + recent + stats over the agent memory store."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.knowledge import MemoryItem, SearchResult, StoreStats
from app.services.memory import get_memory_service

router = APIRouter(tags=["memory"])


@router.get("/search", response_model=list[SearchResult])
def search(q: str, k: int = 5) -> list[SearchResult]:
    """Recall the most relevant memories for a query."""
    return get_memory_service().recall(q, k=k, min_score=0.0)  # type: ignore[return-value]


@router.get("/recent", response_model=list[MemoryItem])
def recent(n: int = 20) -> list[MemoryItem]:
    """Most recently stored memories."""
    return get_memory_service().recent(n)  # type: ignore[return-value]


@router.get("/stats", response_model=StoreStats)
def stats() -> StoreStats:
    return StoreStats(count=get_memory_service().count)
