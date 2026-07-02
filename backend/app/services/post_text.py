"""Shared helper: turn a drafted post into publishable text (caption + hashtags, capped).

Kept dependency-free so every platform publisher can import it without an import cycle.
"""
from __future__ import annotations

from app.schemas.social import SocialDraft


def build_post_text(draft: SocialDraft, limit: int) -> str:
    """caption (or brief) + a hashtag line, trimmed to `limit` characters."""
    base = (draft.caption or draft.brief or "").strip()
    tags = " ".join(
        (t if t.startswith("#") else f"#{t}") for t in (draft.hashtags or []) if t.strip()
    )
    text = (base + (f"\n\n{tags}" if tags else "")).strip()
    return text[:limit]
