"""Knowledge Base routes: search, add, ingest workspace artifacts, stats."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.schemas.knowledge import (
    AddResult,
    IngestResult,
    KnowledgeAddRequest,
    SearchResult,
    StoreStats,
)
from app.services.knowledge import get_knowledge_service

router = APIRouter(tags=["knowledge"])


@router.get("/search", response_model=list[SearchResult])
def search(q: str, k: int = 5) -> list[SearchResult]:
    """Semantic search over the knowledge base."""
    return get_knowledge_service().search(q, k=k)  # type: ignore[return-value]


@router.post("", response_model=AddResult)
def add(req: KnowledgeAddRequest, _user: str = Depends(require_user)) -> AddResult:
    """Add a text document to the knowledge base."""
    item_id = get_knowledge_service().add_text(req.text, source=req.source or "manual", metadata=req.metadata)
    return AddResult(id=item_id)


@router.post("/ingest-workspace", response_model=IngestResult)
def ingest_workspace(_user: str = Depends(require_user)) -> IngestResult:
    """Index every workspace artifact into the knowledge base."""
    svc = get_knowledge_service()
    ingested = svc.ingest_workspace()
    return IngestResult(ingested=ingested, total=svc.count)


@router.get("/stats", response_model=StoreStats)
def stats() -> StoreStats:
    return StoreStats(count=get_knowledge_service().count)
