"""Social platform publishers — real where wired, stub elsewhere (cp-0016 + cp-0020).

YouTube is a REAL OAuth upload of the rendered .mp4 (app.services.youtube), guarded +
stub-safe. The other platforms (Instagram / Facebook / LinkedIn / Twytter) are still
stubs: they record the intent + return a placeholder with a "configure this" note.
``is_configured`` reports whether each platform's credential is present (Integrations
status dots). Publishing is invoked only after human approval.
"""
from __future__ import annotations

from app.schemas.social import PublishResult, SocialDraft
from app.services import facebook, instagram, linkedin, twitter, youtube
from app.services.provider_keys import connector_configured

# platform -> (display label, content kind it serves). Credential status is resolved via the
# social-connector catalog (services/provider_keys) so in-app tokens are honored too.
PLATFORMS: dict[str, tuple[str, str]] = {
    "youtube": ("YouTube", "reel"),
    "instagram": ("Instagram", "reel"),
    "facebook": ("Facebook", "post"),
    "linkedin": ("LinkedIn", "post"),
    "twitter": ("Twitter / X", "post"),
}


def is_configured(platform: str) -> bool:
    """True when the platform's credentials are present (stored in-app OR in env)."""
    return connector_configured(platform)


def status() -> dict[str, bool]:
    """platform -> credential configured? (for the Integrations view)."""
    return {p: is_configured(p) for p in PLATFORMS}


_PUBLISHERS = {
    "youtube": youtube.upload,
    "linkedin": linkedin.publish,
    "facebook": facebook.publish,
    "twitter": twitter.publish,
    "instagram": instagram.publish,
}


async def publish_to(platform: str, draft: SocialDraft) -> PublishResult:
    """Publish a draft to one platform. All five have real, guarded + stub-safe publishers."""
    publisher = _PUBLISHERS.get(platform)
    if publisher is None:
        return PublishResult(platform=platform, ok=False, stub=True, note=f"Unknown platform {platform!r}.")
    return await publisher(draft)
