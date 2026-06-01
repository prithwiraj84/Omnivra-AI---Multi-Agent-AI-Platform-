"""Social content routes (cp-0016): draft reels/posts, list, and approve/reject->publish.

The generate -> human-approval -> publish flow mirrors the workflow approval gate:
drafting returns a SocialDraft with status 'awaiting_approval'; a decision either
rejects it or approves it (which publishes to its target platforms — stubbed in
Phase 1). All routes are project-scoped via the X-Project-Id header (get_project_id).
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response

from app.api.deps import get_project_id, require_user
from app.schemas.social import PostRequest, ReelRequest, SocialDecision, SocialDraft
from app.services.social import get_social_service
from app.services.social_store import get_social_store

router = APIRouter(tags=["social"])


@router.post("/reel", response_model=SocialDraft)
async def draft_reel(req: ReelRequest, project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> SocialDraft:
    """Draft a short-form reel (storyboard + stub voiceover) awaiting approval."""
    return await get_social_service().draft_reel(req.brief, req.targets, project_id)


@router.post("/post", response_model=SocialDraft)
async def draft_post(req: PostRequest, project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> SocialDraft:
    """Draft an image post (FLUX image + caption + tags) awaiting approval."""
    return await get_social_service().draft_post(req.brief, req.targets, project_id)


@router.get("/drafts", response_model=list[SocialDraft])
def list_drafts(project_id: str = Depends(get_project_id)) -> list[SocialDraft]:
    """List the active project's social drafts (newest first)."""
    return get_social_store(project_id).list()


@router.get("/drafts/{draft_id}", response_model=SocialDraft)
def get_draft(draft_id: str, project_id: str = Depends(get_project_id)) -> SocialDraft:
    draft = get_social_store(project_id).get(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail=f"No social draft {draft_id!r}")
    return draft


@router.post("/drafts/{draft_id}/render", response_model=SocialDraft)
def render_reel_draft(
    draft_id: str,
    background_tasks: BackgroundTasks,
    project_id: str = Depends(get_project_id),
    _user: str = Depends(require_user),
) -> SocialDraft:
    """Kick off an async render of a reel draft into an .mp4 (non-blocking).

    Returns immediately with render_status='rendering'; the client polls the draft
    (and watches /ws) for completion. Real .mp4 requires the optional render engine
    (pip install -r requirements-render.txt); without it the storyboard is the output.
    """
    existing = get_social_store(project_id).get(draft_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"No social draft {draft_id!r}")
    if existing.kind != "reel" or existing.storyboard is None:
        raise HTTPException(status_code=400, detail="Only reel drafts can be rendered.")
    if existing.status != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Only drafts awaiting approval can be rendered.")
    svc = get_social_service()
    draft = svc.begin_render(draft_id, project_id)
    if draft is None:  # raced away between the read and begin
        raise HTTPException(status_code=404, detail=f"No social draft {draft_id!r}")
    background_tasks.add_task(svc.run_render, draft_id, project_id)
    return draft


@router.post("/drafts/{draft_id}/decision", response_model=SocialDraft)
async def decide(draft_id: str, decision: SocialDecision, project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> SocialDraft:
    """Approve (-> publish to targets) or reject a drafted piece of content."""
    draft = await get_social_service().decide(draft_id, decision.action, decision.note, project_id)
    if draft is None:
        raise HTTPException(status_code=404, detail=f"No social draft {draft_id!r}")
    return draft


@router.delete("/drafts/{draft_id}", status_code=204)
async def delete_draft(draft_id: str, project_id: str = Depends(get_project_id), _user: str = Depends(require_user)) -> Response:
    """Hard-delete a draft and all of its artifacts (storyboard / b-roll / .mp4 / image / voiceover)."""
    deleted = await get_social_service().delete_draft(draft_id, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No social draft {draft_id!r}")
    return Response(status_code=204)
