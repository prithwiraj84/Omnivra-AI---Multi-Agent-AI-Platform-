"""Google Gemini image generation — the fallback when Hugging Face drops another model.

hf-inference has been steadily retiring models (FLUX.1-schnell went 410 'deprecated', exactly
as every TTS model did before it), so image generation needs a second engine the same way
narration does. Gemini's image models run on the Google AI Studio key most installs already
have for the LLM agents; free-tier quota is tight, so this sits BEHIND Hugging Face rather
than in front — a 429 here falls through to the stub honestly instead of failing the post.
"""
from __future__ import annotations

import base64

import httpx

from app.core.config import get_settings
from app.core.logging import logger
from app.providers.base import (
    FatalProviderError,
    RateLimitError,
    TransientProviderError,
    parse_api_keys,
    with_provider_retry,
)
from app.services.provider_keys import resolve_provider_key

_API = "https://generativelanguage.googleapis.com/v1beta/models"
_TIMEOUT = 120.0

# Tried in order; accounts differ in which image models they can reach.
_MODELS: tuple[str, ...] = (
    "gemini-3.1-flash-image",
    "gemini-2.5-flash-image",
)


def is_configured() -> bool:
    return bool(resolve_provider_key("google_ai"))


def _models() -> list[str]:
    configured = (get_settings().google_image_model or "").strip()
    out = [configured] if configured else []
    return out + [m for m in _MODELS if m != configured]


def _extract_image(payload: dict) -> bytes | None:
    """The first inline image in a generateContent response, or None (e.g. text-only refusal)."""
    for candidate in payload.get("candidates") or []:
        for part in (candidate.get("content") or {}).get("parts") or []:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                try:
                    return base64.b64decode(inline["data"])
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Gemini image: undecodable payload ({})", str(exc)[:120])
                    return None
    return None


@with_provider_retry(max_attempts=2)
async def generate(prompt: str) -> bytes:
    """Generate one image for ``prompt``. Raises so the caller can degrade to a stub."""
    keys = parse_api_keys(resolve_provider_key("google_ai"))
    if not keys:
        raise FatalProviderError("google: no API key configured")

    body = {
        "contents": [{"parts": [{"text": f"Generate an image: {prompt}"}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    last: Exception | None = None
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Model outer, key inner — a model this account can't reach fails identically for every
        # key, whereas a quota 429 is per-key, so rotating keys buys a real second chance.
        for model in _models():
            for key in keys:
                try:
                    resp = await client.post(f"{_API}/{model}:generateContent", params={"key": key}, json=body)
                except httpx.TimeoutException as exc:
                    raise TransientProviderError(f"google: timeout ({exc})") from exc
                except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                    raise TransientProviderError(f"google: connection ({exc})") from exc
                if resp.status_code == 429:
                    last = RateLimitError(f"google {model}: quota exceeded")
                    continue
                if 500 <= resp.status_code < 600:
                    last = TransientProviderError(f"google {model}: {resp.status_code}")
                    continue
                if resp.status_code >= 400:
                    last = FatalProviderError(f"google {model}: {resp.status_code}: {resp.text[:160]}")
                    break  # next MODEL — this one is unreachable for the whole account
                data = _extract_image(resp.json())
                if not data:
                    last = TransientProviderError(f"google {model}: response carried no image")
                    continue
                return data
    raise last or FatalProviderError("google: no image model available on this account")
