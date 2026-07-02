"""Facebook Page publisher — real text post to a Page feed (Graph API), guarded + stub-safe.

Posts the draft's caption/brief (+ hashtags) to the configured Page. Without a Page id +
Page access token it stubs. Never raises: failures return ok=False with a generic note (the
token is never echoed). Mirrors the youtube.py real + stub-safe pattern.
"""
from __future__ import annotations

import httpx

from app.core.logging import logger
from app.schemas.social import PublishResult, SocialDraft
from app.services.post_text import build_post_text
from app.services.provider_keys import connector_configured, resolve_provider_key

_GRAPH = "https://graph.facebook.com/v21.0"
_MAX_CHARS = 60000  # Facebook allows very long posts; cap to keep requests sane


def is_configured() -> bool:
    return connector_configured("facebook")


def _stub(draft: SocialDraft) -> PublishResult:
    return PublishResult(
        platform="facebook",
        ok=True,
        stub=True,
        url=f"https://facebook.local/stub/{draft.id}",
        note="Add a Facebook Page id + token in Integrations to post for real; recorded as a stub.",
    )


async def publish(draft: SocialDraft) -> PublishResult:
    """Publish the draft to the Facebook Page feed. Stub-safe + never raises."""
    if not is_configured():
        return _stub(draft)
    text = build_post_text(draft, _MAX_CHARS)
    if not text:
        return PublishResult(platform="facebook", ok=False, stub=False, note="Nothing to post — the draft has no caption or brief.")
    page_id = resolve_provider_key("facebook_page_id")
    token = resolve_provider_key("facebook_page_token")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_GRAPH}/{page_id}/feed",
                data={"message": text, "access_token": token},
            )
            resp.raise_for_status()
        post_id = resp.json().get("id")
        url = f"https://www.facebook.com/{post_id}" if post_id else None
        return PublishResult(platform="facebook", ok=True, stub=False, url=url, note="Posted to your Facebook Page.")
    except Exception as exc:  # noqa: BLE001
        logger.error("Facebook post failed ({}): {}", type(exc).__name__, str(exc)[:200])
        return PublishResult(platform="facebook", ok=False, stub=False, note=f"Facebook post failed ({type(exc).__name__}); see server logs.")
