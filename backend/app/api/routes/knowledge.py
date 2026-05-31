"""Knowledge Base routes: search, add, ingest workspace artifacts, stats."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_project_id, require_user
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
def search(q: str, k: int = 5, project_id: str = Depends(get_project_id)) -> list[SearchResult]:
    """Semantic search over the active project's knowledge base."""
    return get_knowledge_service(project_id).search(q, k=k)  # type: ignore[return-value]


@router.post("", response_model=AddResult)
def add(req: KnowledgeAddRequest, project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> AddResult:
    """Add a text document to the active project's knowledge base."""
    item_id = get_knowledge_service(project_id).add_text(req.text, source=req.source or "manual", metadata=req.metadata)
    return AddResult(id=item_id)


@router.post("/ingest-workspace", response_model=IngestResult)
def ingest_workspace(project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> IngestResult:
    """Index the active project's workspace artifacts into its knowledge base."""
    svc = get_knowledge_service(project_id)
    ingested = svc.ingest_workspace()
    return IngestResult(ingested=ingested, total=svc.count)


@router.get("/stats", response_model=StoreStats)
def stats(project_id: str = Depends(get_project_id)) -> StoreStats:
    return StoreStats(count=get_knowledge_service(project_id).count)
