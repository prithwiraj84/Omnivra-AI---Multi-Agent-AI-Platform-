"""Pexels client (cp-0018) — stock b-roll for reels AND stock photos, stub-safe.

Without PEXELS_API_KEY every call returns None, so the reel renderer falls back to
generated color backgrounds (a fully-offline render). With a key it searches for a
portrait clip per scene and downloads it into the project workspace. Network calls
use the shared tenacity retry policy.

PHOTOS (cp-0076) are the last real option in the image chain: when every generation
engine is down (hf-inference retires models regularly; Gemini's free image quota is
tight), a RELEVANT licensed photograph beats a placeholder .txt. Pexels is used rather
than scraping a search engine for two reasons that matter here: its license explicitly
permits commercial use — and this pipeline PUBLISHES to Instagram/LinkedIn/YouTube, so
image rights are a real exposure, not a formality — and it is an API, so it needs no
browser engine and works unchanged on a shared host.
"""
from __future__ import annotations

import asyncio
import re
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
_PHOTO_SEARCH_URL = "https://api.pexels.com/v1/search"


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


# --- photo search -----------------------------------------------------------------------------
# A generation PROMPT and a stock-photo QUERY are different things. Prompts are long, styled
# sentences ("High-quality social media marketing image for: launch our AI company OS. Clean,
# modern, brand-forward, vibrant.") and Pexels matches those against almost nothing. A search
# wants 2-4 concrete words, so the prompt is distilled before it is sent — this is the whole
# difference between a RELEVANT photo and an empty result set.
_PROMPT_BOILERPLATE = re.compile(
    r"\b(high[- ]?quality|professional|photo(?:graph)?\s+of|an?\s+image\s+of|generate\s+an?\s+image|"
    r"social\s+media|marketing\s+image|illustration|render(?:ing)?|wallpaper|background|"
    r"brand[- ]?forward|clean|modern|minimal(?:ist)?|vibrant|stylish|sleek|beautiful|stunning|"
    r"4k|8k|hd|ultra|detailed|realistic|cinematic|studio\s+lighting)\b",
    re.IGNORECASE,
)
# Ordinary connective words carry no visual meaning; a query full of them dilutes the match.
_STOPWORDS = frozenset("""
a an the and or but for nor of to in on at by with from into about as is are was were be been
being this that these those it its our your their his her my we you they i he she them us
create make build show design need want using use via like new best top great good very more
most some any all can will would should could please help me my our
""".split())
# Used when a prompt yields nothing searchable — e.g. a Devanagari brief, since Pexels only
# indexes English (the same constraint the reel b-roll queries live under).
_GENERIC_QUERY = "modern technology abstract"
_MAX_QUERY_WORDS = 4


def photo_query(prompt: str, *, max_words: int = _MAX_QUERY_WORDS) -> str:
    """Distil an image PROMPT into a Pexels search query (2-4 meaningful words).

    Order is preserved — the subject of a prompt usually comes before its modifiers — and a
    prompt with nothing searchable (non-Latin script, pure styling words) degrades to a
    generic visual query rather than returning nothing at all.
    """
    text = _PROMPT_BOILERPLATE.sub(" ", prompt or "")
    words: list[str] = []
    for raw in re.findall(r"[A-Za-z][A-Za-z0-9'-]*", text):
        word = raw.lower().strip("'-")
        if len(word) < 3 or word in _STOPWORDS or word in words:
            continue
        words.append(word)
        if len(words) >= max_words:
            break
    return " ".join(words) or _GENERIC_QUERY


# Which rendition to download, best first. Pexels caps `large` at 940x650 — under Instagram's
# 1080px feed width, so it would upscale and soften. `large2x` is 1880x1300 (~600 KB) which
# publishes cleanly at a fraction of `original` (routinely 6000px / 4 MB, a waste to fetch,
# store on an ephemeral disk, and upload).
_SRC_PREFERENCE = ("large2x", "large", "original", "medium")


def _photo_url(photo: dict) -> str | None:
    """The best available rendition URL for a photo."""
    src = photo.get("src") or {}
    return next((src[k] for k in _SRC_PREFERENCE if src.get(k)), None)


def _pick_photo(photos: list[dict], *, min_width: int = 800) -> dict | None:
    """The best usable photo: large enough to publish, largest first."""
    usable = [p for p in photos if (p.get("width") or 0) >= min_width and _photo_url(p)]
    if not usable:
        usable = [p for p in photos if _photo_url(p)]
    return max(usable, key=lambda p: (p.get("width") or 0) * (p.get("height") or 0), default=None)


@with_provider_retry(max_attempts=3)
async def _search_photos(query: str, orientation: str) -> list[dict]:
    key = resolve_provider_key("pexels")
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                _PHOTO_SEARCH_URL,
                headers={"Authorization": key or ""},
                params={"query": query, "orientation": orientation, "per_page": 5},
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
    return resp.json().get("photos", []) or []


# A TOTAL budget for the whole fallback, enforced regardless of how the parts interact. Without
# it the worst case multiplies out badly: 3 broadening attempts x 3 tenacity retries x a 20s
# timeout, plus the download — well past the frontend's 180s request timeout, on a request path
# (drafting a post) that has ALREADY spent time failing two generators. A stub arriving promptly
# beats a photo arriving after the browser gave up.
_PHOTO_BUDGET_SECONDS = 45.0
# Magic bytes of the formats Pexels actually serves. `raise_for_status` catches 4xx/5xx, but a
# 200 carrying an HTML interstitial would otherwise be written to disk as a .png and render as
# a broken image with no error anywhere.
_IMAGE_MAGIC = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF8", b"RIFF")


def _looks_like_image(data: bytes) -> bool:
    return bool(data) and data.startswith(_IMAGE_MAGIC)


async def _fetch_photo(prompt: str, orientation: str) -> tuple[bytes, str] | None:
    query = photo_query(prompt)
    # Narrow first, then progressively broader — the last attempt is the generic query, so a
    # configured key essentially always returns SOMETHING publishable. De-duplicated so a
    # one-word prompt can't spend an attempt searching the same thing twice.
    attempts: list[str] = []
    for candidate in (query, " ".join(query.split()[:2]), _GENERIC_QUERY):
        if candidate and candidate not in attempts:
            attempts.append(candidate)

    photo = None
    for attempt in attempts:
        try:
            photo = _pick_photo(await _search_photos(attempt, orientation))
        except Exception as exc:  # noqa: BLE001 - one dead query must not end the walk
            logger.warning("Pexels photo search failed for {!r}: {}", attempt, str(exc)[:160])
            continue
        if photo:
            break
    if not photo:
        return None

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(_photo_url(photo) or "")
        resp.raise_for_status()
    if not _looks_like_image(resp.content):
        logger.warning("Pexels returned a non-image body for {!r}; ignoring", query)
        return None
    # Pexels doesn't require attribution, but recording the photographer keeps the artifact
    # honest about where the image came from (and is what their guidelines ask for).
    return resp.content, f"{photo.get('photographer') or 'Pexels'} on Pexels"


async def fetch_photo(prompt: str, *, orientation: str = "landscape") -> tuple[bytes, str] | None:
    """Find a licensed stock photo for ``prompt``; returns ``(image_bytes, credit)`` or None.

    Falls back to a broader query before giving up: a 4-word search can be too specific to
    match anything, and a relevant-ish photo still beats a placeholder. Never raises, and never
    runs longer than ``_PHOTO_BUDGET_SECONDS``.
    """
    if not is_configured():
        return None
    try:
        return await asyncio.wait_for(_fetch_photo(prompt, orientation), timeout=_PHOTO_BUDGET_SECONDS)
    except asyncio.TimeoutError:
        logger.warning("Pexels photo fallback exceeded its {}s budget; writing a stub", _PHOTO_BUDGET_SECONDS)
        return None
    except Exception as exc:  # noqa: BLE001 - stock photos are best-effort; degrade to a stub
        logger.warning("Pexels photo fetch failed: {}", repr(exc))
        return None
