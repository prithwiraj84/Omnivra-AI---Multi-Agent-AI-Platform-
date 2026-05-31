"""Social platform publishers — real where wired, stub elsewhere (cp-0016 + cp-0020).

YouTube is a REAL OAuth upload of the rendered .mp4 (app.services.youtube), guarded +
stub-safe. The other platforms (Instagram / Facebook / LinkedIn / Twytter) are still
stubs: they record the intent + return a placeholder with a "configure this" note.
``is_configured`` reports whether each platform's credential is present (Integrations
status dots). Publishing is invoked only after human approval.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.schemas.social import PublishResult, SocialDraft
from app.services import youtube

# platform -> (display label, settings attr holding its credential, content kind it serves)
PLATFORMS: dict[str, tuple[str, str, str]] = {
    "youtube": ("YouTube", "youtube_refresh_token", "reel"),
    "instagram": ("Instagram", "instagram_access_token", "reel"),
    "facebook": ("Facebook", "facebook_page_token", "post"),
    "linkedin": ("LinkedIn", "linkedin_access_token", "post"),
    "twitter": ("Twitter / X", "twitter_bearer_token", "post"),
}


def is_configured(platform: str) -> bool:
    if platform == "youtube":
        return youtube.is_configured()
    spec = PLATFORMS.get(platform)
    return bool(getattr(get_settings(), spec[1], None)) if spec else False


def status() -> dict[str, bool]:
    """platform -> credential configured? (for the Integrations view)."""
    return {p: is_configured(p) for p in PLATFORMS}


async def publish_to(platform: str, draft: SocialDraft) -> PublishResult:
    """Publish a draft to one platform. YouTube is a real upload; the rest stub for now."""
    if platform == "youtube":
        return await youtube.upload(draft)

    spec = PLATFORMS.get(platform)
    if not spec:
        return PublishResult(platform=platform, ok=False, stub=True, note=f"Unknown platform {platform!r}.")
    label, attr, _kind = spec
    configured = bool(getattr(get_settings(), attr, None))
    note = (
        f"{label} credential present; real upload is wired in a later phase (recorded as a stub)."
        if configured
        else f"Set {attr.upper()} to publish to {label} for real; recorded as a stub."
    )
    return PublishResult(platform=platform, ok=True, url=f"https://{platform}.local/stub/{draft.id}", stub=True, note=note)
