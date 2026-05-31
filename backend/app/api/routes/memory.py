"""Memory routes: recall (search) + recent + stats over the agent memory store."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_project_id
from app.schemas.knowledge import MemoryItem, SearchResult, StoreStats
from app.services.memory import get_memory_service

router = APIRouter(tags=["memory"])


@router.get("/search", response_model=list[SearchResult])
def search(q: str, k: int = 5, project_id: str = Depends(get_project_id)) -> list[SearchResult]:
    """Recall the most relevant memories for a query (within the active project)."""
    return get_memory_service(project_id).recall(q, k=k, min_score=0.0)  # type: ignore[return-value]


@router.get("/recent", response_model=list[MemoryItem])
def recent(n: int = 20, project_id: str = Depends(get_project_id)) -> list[MemoryItem]:
    """Most recently stored memories in the active project."""
    return get_memory_service(project_id).recent(n)  # type: ignore[return-value]


@router.get("/stats", response_model=StoreStats)
def stats(project_id: str = Depends(get_project_id)) -> StoreStats:
    return StoreStats(count=get_memory_service(project_id).count)
