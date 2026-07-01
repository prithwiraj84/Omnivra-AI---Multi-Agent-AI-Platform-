"""Pexels Video API client (cp-0018) — stock b-roll for reels, stub-safe.

Without PEXELS_API_KEY every call returns None, so the reel renderer falls back to
generated color backgrounds (a fully-offline render). With a key it searches for a
portrait clip per scene and downloads it into the project workspace. Network calls
use the shared tenacity retry policy.
"""
from __future__ import annotations

from pathlib import Path

import httpx

from app.core.logging import logger
from app.providers.base import (
    FatalProviderError,
    RateLimitError,
    TransientProviderError,
    with_provider_retry,
)
from app.services.provider_keys import resolve_provider_key

_SEARCH_URL = "https://api.pexels.com/videos/search"


def is_configured() -> bool:
    return bool(resolve_provider_key("pexels"))


def _pick_portrait_link(videos: list[dict]) -> str | None:
    """From a Pexels videos[] response pick a reasonably-sized portrait mp4 link."""
    for vid in videos:
        files = [f for f in vid.get("video_files", []) if (f.get("file_type") or "").endswith("mp4")]
        # prefer portrait (h > w), then the smallest such (faster download / render)
        portrait = [f for f in files if (f.get("height") or 0) >= (f.get("width") or 0)]
        chosen = sorted(portrait or files, key=lambda f: (f.get("width") or 0) * (f.get("height") or 0))
        if chosen:
            return chosen[0].get("link")
    return None


@with_provider_retry(max_attempts=3)
async def _search(query: str) -> str | None:
    key = resolve_provider_key("pexels")
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                _SEARCH_URL,
                headers={"Authorization": key or ""},
                params={"query": query, "orientation": "portrait", "per_page": 3},
            )
    except httpx.TimeoutException as exc:
        raise TransientProviderError(f"timeout: {exc}") from exc
    except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
        raise TransientProviderError(f"connection: {exc}") from exc
    if resp.status_code == 429:
        raise RateLimitError(resp.text[:200])
    if 500 <= resp.status_code < 600:
        raise TransientProviderError(f"{resp.status_code}")
    if resp.status_code >= 400:
        raise FatalProviderError(f"{resp.status_code}: {resp.text[:160]}")
    return _pick_portrait_link(resp.json().get("videos", []))


async def fetch_broll(query: str, dest: Path) -> Path | None:
    """Search + download one portrait clip for ``query`` to ``dest``. None if unavailable.

    Never raises: any failure (no key, no match, network) returns None so the render
    falls back to a color background for that scene.
    """
    if not is_configured() or not query.strip():
        return None
    try:
        link = await _search(query)
        if not link:
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(link)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        return dest
    except Exception as exc:  # noqa: BLE001 - b-roll is best-effort; degrade to color bg
        logger.warning("Pexels b-roll fetch failed for {!r} (using color bg): {}", query, repr(exc))
        return None
