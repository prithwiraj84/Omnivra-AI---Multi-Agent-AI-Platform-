"""Document Studio routes (cp-0025): generate a document, list, get, approve/reject.

Generate -> human-approval mirrors the social pipeline: generating returns a
DocumentDraft with status 'awaiting_approval' and a rendered file; a decision
approves or rejects it. The rendered file downloads via GET /api/workspace/media.
All routes are project-scoped via the X-Project-Id header (get_project_id).
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.deps import get_project_id, require_user
from app.schemas.documents import DocumentDecision, DocumentDraft, DocumentRequest
from app.services.document_store import get_document_store
from app.services.documents import get_document_service

router = APIRouter(tags=["documents"])


@router.post("/generate", response_model=DocumentDraft)
def generate(
    req: DocumentRequest,
    background_tasks: BackgroundTasks,
    project_id: str = Depends(get_project_id),
    _user: str = Depends(require_user),
) -> DocumentDraft:
    """Kick off document generation; returns IMMEDIATELY with a 'generating' draft.

    Gemma writing the content + rendering the file can take many seconds (longer when a provider
    is rate-limited), so it runs in a BackgroundTask and the client polls GET /api/documents until
    the draft leaves 'generating' (-> 'awaiting_approval'). Avoids the request-timeout failure.
    """
    svc = get_document_service()
    pending = svc.begin_document(req.prompt, req.format, req.theme, req.style, req.font, project_id)
    background_tasks.add_task(svc.generate_document, pending.id, req.prompt, pending.format, req.theme, req.style, req.font, project_id)
    return pending


@router.get("", response_model=list[DocumentDraft])
def list_documents(project_id: str = Depends(get_project_id)) -> list[DocumentDraft]:
    """List the active project's document drafts (newest first)."""
    return get_document_store(project_id).list()


@router.get("/{doc_id}", response_model=DocumentDraft)
def get_document(doc_id: str, project_id: str = Depends(get_project_id)) -> DocumentDraft:
    draft = get_document_store(project_id).get(doc_id)
    if draft is None:
        raise HTTPException(status_code=404, detail=f"No document {doc_id!r}")
    return draft


@router.post("/{doc_id}/decision", response_model=DocumentDraft)
async def decide(doc_id: str, decision: DocumentDecision, project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> DocumentDraft:
    """Approve or reject a drafted document."""
    draft = await get_document_service().decide(doc_id, decision.action, decision.note, project_id)
    if draft is None:
        raise HTTPException(status_code=404, detail=f"No document {doc_id!r}")
    return draft
