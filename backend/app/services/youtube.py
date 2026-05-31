"""YouTube Data API v3 uploader (cp-0020) — real, guarded, stub-safe.

Uploads a rendered reel .mp4 via OAuth2 (a long-lived refresh token -> short-lived
access token, no interactive runtime flow) + a resumable upload. Without
YOUTUBE_CLIENT_ID / _SECRET / _REFRESH_TOKEN it reports unconfigured and the
publisher stubs (so the whole flow still runs offline). Videos upload as PRIVATE by
default — a human flips them to Public on YouTube after review (matches the approval
ethos). Never raises: failures return ok=False with a note. See docs/SOCIAL_PUBLISHING.md.
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import logger
from app.providers.base import (
    FatalProviderError,
    RateLimitError,
    TransientProviderError,
    with_provider_retry,
)
from app.schemas.social import PublishResult, SocialDraft
from app.workspace_fs.paths import project_root

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
_VIDEO_MIME = "video/mp4"  # the render engine always writes .mp4
_MAX_UPLOAD_BYTES = 1024 * 1024 * 1024  # 1 GB guard (reels are tiny; prevents an OOM read)


def is_configured() -> bool:
    s = get_settings()
    return bool(s.youtube_client_id and s.youtube_client_secret and s.youtube_refresh_token)


@with_provider_retry(max_attempts=3)
async def _access_token() -> str:
    """Exchange the refresh token for a short-lived access token."""
    s = get_settings()
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            _TOKEN_URL,
            data={
                "client_id": s.youtube_client_id,
                "client_secret": s.youtube_client_secret,
                "refresh_token": s.youtube_refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if resp.status_code == 429:
        raise RateLimitError(resp.text[:200])
    if 500 <= resp.status_code < 600:
        raise TransientProviderError(f"{resp.status_code}")
    if resp.status_code >= 400:
        raise FatalProviderError(f"token exchange {resp.status_code}: {resp.text[:160]}")
    return resp.json()["access_token"]


def _stub(draft: SocialDraft) -> PublishResult:
    return PublishResult(
        platform="youtube",
        ok=True,
        stub=True,
        url=f"https://youtube.local/stub/{draft.id}",
        note="Set YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN to upload for real; recorded as a stub.",
    )


async def upload(draft: SocialDraft) -> PublishResult:
    """Upload the draft's rendered .mp4 to YouTube (private). Stub-safe + never raises."""
    if not is_configured():
        return _stub(draft)
    if not draft.video_path:
        return PublishResult(platform="youtube", ok=False, stub=False, note="Render the reel to an .mp4 before publishing to YouTube.")
    video = project_root(draft.project_id) / draft.video_path
    if not video.is_file():
        return PublishResult(platform="youtube", ok=False, stub=False, note="Rendered video is missing; re-render before publishing.")

    try:
        token = await _access_token()
        title = ((draft.storyboard.title if draft.storyboard else "") or draft.brief or "Omnivra reel").strip()[:100]
        description = " ".join([draft.brief, *(draft.hashtags or [])]).strip()[:4900]
        tags = [h.lstrip("#") for h in (draft.hashtags or []) if h.strip()][:15]
        metadata = {
            "snippet": {"title": title or "Omnivra reel", "description": description, "tags": tags},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False},
        }
        size = video.stat().st_size
        if size > _MAX_UPLOAD_BYTES:
            return PublishResult(platform="youtube", ok=False, stub=False, note=f"Video is {size // (1024 * 1024)}MB; exceeds the {_MAX_UPLOAD_BYTES // (1024 * 1024)}MB upload cap.")
        data = video.read_bytes()
        async with httpx.AsyncClient(timeout=180.0) as client:
            # 1) Initiate a resumable upload session (concrete MIME, not a wildcard).
            init = await client.post(
                _UPLOAD_URL,
                params={"uploadType": "resumable", "part": "snippet,status"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-Upload-Content-Type": _VIDEO_MIME,
                    "X-Upload-Content-Length": str(size),
                },
                json=metadata,
            )
            init.raise_for_status()
            location = init.headers.get("Location") or init.headers.get("location")
            if not location:
                return PublishResult(platform="youtube", ok=False, stub=False, note="YouTube did not return an upload URL.")
            # 2) Upload the bytes (explicit Content-Type + Content-Length per the resumable spec).
            put = await client.put(
                location,
                headers={"Content-Type": _VIDEO_MIME, "Content-Length": str(size)},
                content=data,
            )
            put.raise_for_status()
            try:
                video_id = put.json().get("id")
            except ValueError:  # non-JSON body
                video_id = None
        if not video_id:
            return PublishResult(platform="youtube", ok=False, stub=False, note="YouTube accepted the upload but returned no video id.")
        return PublishResult(
            platform="youtube",
            ok=True,
            stub=False,
            url=f"https://www.youtube.com/watch?v={video_id}",
            note="Uploaded as PRIVATE — review on YouTube, then set to Public when ready.",
        )
    except Exception as exc:  # noqa: BLE001 - never let an upload crash the publish loop
        # Server log gets the type + truncated message (Google never echoes the secret/
        # refresh token in error bodies, and httpx errors don't include the request body).
        # The persisted/UI-facing note stays generic — never raw exception text.
        logger.error("YouTube upload failed ({}): {}", type(exc).__name__, str(exc)[:200])
        return PublishResult(
            platform="youtube",
            ok=False,
            stub=False,
            note=f"YouTube upload failed ({type(exc).__name__}); see server logs.",
        )
