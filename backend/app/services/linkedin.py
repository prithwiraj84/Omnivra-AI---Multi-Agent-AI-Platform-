"""LinkedIn publisher — real text post via the UGC Posts API, guarded + stub-safe.

Posts the draft's caption/brief (+ hashtags) to the signed-in member's feed as PUBLIC.
Without a LinkedIn access token it reports unconfigured and the publisher stubs, so the
approve → publish flow still completes offline. Never raises: failures return ok=False with
a generic note (the token is never echoed). Mirrors the youtube.py real + stub-safe pattern.
"""
from __future__ import annotations

import httpx

from app.core.logging import logger
from app.schemas.social import PublishResult, SocialDraft
from app.services.post_text import build_post_text
from app.services.provider_keys import connector_configured, resolve_provider_key

_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"  # OpenID → member id (sub)
_UGC_URL = "https://api.linkedin.com/v2/ugcPosts"
_MAX_CHARS = 3000


def is_configured() -> bool:
    return connector_configured("linkedin")


def _stub(draft: SocialDraft) -> PublishResult:
    return PublishResult(
        platform="linkedin",
        ok=True,
        stub=True,
        url=f"https://linkedin.local/stub/{draft.id}",
        note="Add a LinkedIn access token in Integrations to post for real; recorded as a stub.",
    )


async def publish(draft: SocialDraft) -> PublishResult:
    """Publish the draft as a LinkedIn text share. Stub-safe + never raises."""
    if not is_configured():
        return _stub(draft)
    text = build_post_text(draft, _MAX_CHARS)
    if not text:
        return PublishResult(platform="linkedin", ok=False, stub=False, note="Nothing to post — the draft has no caption or brief.")
    token = resolve_provider_key("linkedin_access_token")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1) Resolve the author URN from the token (needs the openid/profile scopes).
            who = await client.get(_USERINFO_URL, headers={"Authorization": f"Bearer {token}"})
            who.raise_for_status()
            sub = who.json().get("sub")
            if not sub:
                return PublishResult(platform="linkedin", ok=False, stub=False, note="Could not resolve your LinkedIn member id (the token needs the openid + profile scopes).")
            # 2) Create the share.
            body = {
                "author": f"urn:li:person:{sub}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }
            resp = await client.post(
                _UGC_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
        urn = resp.headers.get("x-restli-id") or resp.json().get("id")
        url = f"https://www.linkedin.com/feed/update/{urn}" if urn else None
        return PublishResult(platform="linkedin", ok=True, stub=False, url=url, note="Posted to LinkedIn.")
    except Exception as exc:  # noqa: BLE001 — never let a publish crash the run
        logger.error("LinkedIn post failed ({}): {}", type(exc).__name__, str(exc)[:200])
        return PublishResult(platform="linkedin", ok=False, stub=False, note=f"LinkedIn post failed ({type(exc).__name__}); see server logs.")
