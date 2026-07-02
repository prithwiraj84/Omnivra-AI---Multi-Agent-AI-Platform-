"""Instagram Reels publisher — real publish via the Graph API, guarded + stub-safe.

Instagram *pulls* the video from a public URL, so we first upload the rendered `.mp4` to
Supabase Storage (a temporary signed URL), then run the container flow:
  1. POST /{ig_user}/media  (media_type=REELS, video_url, caption) -> creation_id
  2. poll GET /{creation_id}?fields=status_code until FINISHED (IG transcodes async)
  3. POST /{ig_user}/media_publish (creation_id) -> media id -> permalink

Without IG creds it stubs; with creds but no Supabase Storage it returns a clear note (no
network). Never raises: failures return ok=False + a generic note (tokens are never echoed).
"""
from __future__ import annotations

import asyncio

import httpx

from app.core.logging import logger
from app.schemas.social import PublishResult, SocialDraft
from app.services import storage
from app.services.post_text import build_post_text
from app.services.provider_keys import connector_configured, resolve_provider_key
from app.workspace_fs.paths import project_root

_GRAPH = "https://graph.facebook.com/v21.0"
_MAX_CHARS = 2200  # IG caption limit
_MAX_UPLOAD_BYTES = 1024 * 1024 * 1024  # 1 GB guard (reels are tiny)
_POLL_ATTEMPTS = 12
_POLL_INTERVAL = 5.0  # seconds -> up to ~60s waiting for IG to finish transcoding


def is_configured() -> bool:
    return connector_configured("instagram")


def _stub(draft: SocialDraft) -> PublishResult:
    return PublishResult(
        platform="instagram",
        ok=True,
        stub=True,
        url=f"https://instagram.local/stub/{draft.id}",
        note="Add Instagram credentials in Integrations to publish for real; recorded as a stub.",
    )


async def _wait_ready(client: httpx.AsyncClient, creation_id: str, token: str) -> str:
    """Poll the container until it's FINISHED (or the last-seen status when we give up)."""
    status = "IN_PROGRESS"
    for _ in range(_POLL_ATTEMPTS):
        resp = await client.get(
            f"{_GRAPH}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
        )
        resp.raise_for_status()
        status = resp.json().get("status_code", "IN_PROGRESS")
        if status in ("FINISHED", "ERROR", "EXPIRED"):
            return status
        await asyncio.sleep(_POLL_INTERVAL)
    return status


async def publish(draft: SocialDraft) -> PublishResult:
    """Publish the draft's rendered reel to Instagram. Stub-safe + never raises."""
    if not is_configured():
        return _stub(draft)
    if not draft.video_path:
        return PublishResult(platform="instagram", ok=False, stub=False, note="Render the reel to an .mp4 before publishing to Instagram.")
    video = project_root(draft.project_id) / draft.video_path
    if not video.is_file():
        return PublishResult(platform="instagram", ok=False, stub=False, note="Rendered video is missing; re-render before publishing.")
    if video.stat().st_size > _MAX_UPLOAD_BYTES:
        return PublishResult(platform="instagram", ok=False, stub=False, note="Video exceeds the 1GB upload cap.")
    if not storage.is_configured():
        return PublishResult(
            platform="instagram",
            ok=False,
            stub=False,
            note="Instagram needs the reel at a public URL. Configure Supabase Storage (SUPABASE_URL + service-role key + a bucket) to enable it.",
        )

    ig_user = resolve_provider_key("instagram_user_id")
    token = resolve_provider_key("instagram_access_token")
    caption = build_post_text(draft, _MAX_CHARS)
    try:
        public_url = await storage.upload_signed(video, f"reels/{draft.id}.mp4", content_type="video/mp4")
        if not public_url:
            return PublishResult(platform="instagram", ok=False, stub=False, note="Could not host the reel for Instagram to fetch (Supabase Storage upload returned no URL).")
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1) create the reel container
            create = await client.post(
                f"{_GRAPH}/{ig_user}/media",
                data={"media_type": "REELS", "video_url": public_url, "caption": caption, "access_token": token},
            )
            create.raise_for_status()
            creation_id = create.json().get("id")
            if not creation_id:
                return PublishResult(platform="instagram", ok=False, stub=False, note="Instagram did not return a media container id.")
            # 2) wait for transcoding
            status = await _wait_ready(client, creation_id, token or "")
            if status != "FINISHED":
                return PublishResult(platform="instagram", ok=False, stub=False, note=f"Instagram is still processing the reel (status {status}); approve → publish again shortly to finish.")
            # 3) publish
            pub = await client.post(
                f"{_GRAPH}/{ig_user}/media_publish",
                data={"creation_id": creation_id, "access_token": token},
            )
            pub.raise_for_status()
            media_id = pub.json().get("id")
            # 4) best-effort permalink
            url = None
            if media_id:
                try:
                    perma = await client.get(f"{_GRAPH}/{media_id}", params={"fields": "permalink", "access_token": token})
                    if perma.status_code < 400:
                        url = perma.json().get("permalink")
                except Exception:  # noqa: BLE001 — permalink is optional
                    url = None
        return PublishResult(platform="instagram", ok=True, stub=False, url=url, note="Published reel to Instagram.")
    except Exception as exc:  # noqa: BLE001
        logger.error("Instagram publish failed ({}): {}", type(exc).__name__, str(exc)[:200])
        return PublishResult(platform="instagram", ok=False, stub=False, note=f"Instagram publish failed ({type(exc).__name__}); see server logs.")
