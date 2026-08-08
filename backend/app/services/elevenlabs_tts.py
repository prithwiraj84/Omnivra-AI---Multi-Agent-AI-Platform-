"""ElevenLabs text-to-speech — the high-fidelity narration path for reels.

Groq's speech models are fast and free but sound synthetic AND are English-only; ElevenLabs is
what makes a reel sound like a real person, and its multilingual models are what let a Hindi
script actually be spoken in Hindi. It is entirely OPTIONAL: with no key configured
`is_configured()` is False and the media service falls straight through to the rest of the
chain, so nothing regresses for users who don't set it up.

The key is resolved through the normal per-user provider-key path, so each signed-in user can
bring their own ElevenLabs account (Integrations → API keys) exactly like their LLM keys.
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
from app.services.languages import get_language
from app.services.provider_keys import resolve_provider_key

_API = "https://api.elevenlabs.io/v1"
# mp3 is what the API returns by default and what ffmpeg/moviepy read most reliably.
_OUTPUT_FORMAT = "mp3_44100_128"
AUDIO_EXT = "mp3"
_TIMEOUT = 120.0  # a full scene of narration; generation happens off the request path

# The model to fall back to when the configured one can't speak the requested language.
_MULTILINGUAL_MODEL = "eleven_multilingual_v2"
# Models that only speak English. Handing them Hindi produces mangled audio rather than an
# error, so we silently upgrade to a multilingual model instead of "succeeding" with garbage.
_ENGLISH_ONLY_MODELS = frozenset({
    "eleven_monolingual_v1",
    "eleven_english_sts_v2",
    "eleven_turbo_v2",
})
# Only these accept an explicit `language_code`; sending it to the others is a 422.
_LANGUAGE_CODE_MODELS = frozenset({"eleven_turbo_v2_5", "eleven_flash_v2_5"})


def is_configured() -> bool:
    return bool(resolve_provider_key("elevenlabs"))


def _model_for(language: str) -> str:
    """The model to use for ``language`` — upgraded to multilingual when the configured one
    can't speak it."""
    configured = (get_settings().elevenlabs_model or _MULTILINGUAL_MODEL).strip()
    lang = get_language(language)
    if lang.elevenlabs_needs_multilingual and configured in _ENGLISH_ONLY_MODELS:
        logger.info(
            "ElevenLabs: {} is English-only; using {} for {} narration",
            configured, _MULTILINGUAL_MODEL, lang.name,
        )
        return _MULTILINGUAL_MODEL
    return configured


def _configured_voice_for(language: str) -> str:
    """The pinned voice id for ``language``: a per-language override, else the general one.

    Lets a user keep an English narrator and a Hindi narrator side by side
    (ELEVENLABS_VOICE_ID + ELEVENLABS_VOICE_ID_HI) instead of re-pointing one setting.
    """
    s = get_settings()
    per_language = {"hi": s.elevenlabs_voice_id_hi}.get(get_language(language).code)
    return ((per_language or "").strip()) or ((s.elevenlabs_voice_id or "").strip())


async def _resolve_voice_id(client: httpx.AsyncClient, key: str, language: str) -> str | None:
    """The configured voice for this language, or the account's first available one.

    Falling back to whatever the account actually has means TTS works out of the box instead of
    failing on a hardcoded voice id the user may not own.
    """
    configured = _configured_voice_for(language)
    if configured:
        return configured
    try:
        resp = await client.get(f"{_API}/voices", headers={"xi-api-key": key})
        resp.raise_for_status()
        voices = resp.json().get("voices") or []
        return str(voices[0]["voice_id"]) if voices else None
    except Exception as exc:  # noqa: BLE001 - treated as "no voice available"
        logger.warning("ElevenLabs: could not list voices ({})", str(exc)[:160])
        return None


@with_provider_retry(max_attempts=2)
async def synthesize(text: str, *, language: str = "en") -> bytes:
    """Synthesize ``text`` to mp3 bytes in ``language``.

    Raises on failure so the caller can fall through to the next engine in the chain.
    """
    key = resolve_provider_key("elevenlabs")
    if not key:
        raise FatalProviderError("elevenlabs: no API key configured")
    lang = get_language(language)
    model = _model_for(lang.code)

    body: dict[str, object] = {
        "text": text,
        "model_id": model,
        # Settings tuned for narration: stable enough not to wander between scenes, with
        # enough style for it to sound spoken rather than read.
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True},
    }
    # Only the v2.5 models accept this; multilingual_v2 detects the language from the text.
    if model in _LANGUAGE_CODE_MODELS:
        body["language_code"] = lang.code

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        voice_id = await _resolve_voice_id(client, key, lang.code)
        if not voice_id:
            raise FatalProviderError("elevenlabs: no voice available on this account")
        resp = await client.post(
            f"{_API}/text-to-speech/{voice_id}",
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            params={"output_format": _OUTPUT_FORMAT},
            json=body,
        )

    if resp.status_code == 429:
        raise RateLimitError(resp.text[:200])
    if 500 <= resp.status_code < 600:
        raise TransientProviderError(f"{resp.status_code}: {resp.text[:120]}")
    if resp.status_code >= 400:
        raise FatalProviderError(f"{resp.status_code}: {resp.text[:200]}")
    return resp.content


def describe(language: str = "en") -> str:
    """Human-readable engine label for a render note."""
    return f"ElevenLabs ({_model_for(language)})"
