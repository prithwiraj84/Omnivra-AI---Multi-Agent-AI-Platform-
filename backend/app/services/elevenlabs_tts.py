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


# Voice categories a FREE account can actually synthesize with, best first. Voices added from
# the Voice Library are rejected with 402 paid_plan_required ("Free users cannot use library
# voices"), so picking "the account's first voice" blindly breaks every free account whose
# library list happens to sort first.
_USABLE_CATEGORIES: tuple[str, ...] = ("premade", "cloned", "generated")
# Last-resort global defaults, for keys that can't list voices at all (a permission-scoped key
# 401s on /v1/voices while still being able to synthesize). Several are needed, not one: which
# premade voices a free plan may use has narrowed over time — Rachel now 402s on free accounts
# while Adam still works — so the list is ordered by what verified free-tier access most
# recently, and the walk stops at the first that returns audio.
_DEFAULT_VOICE_IDS: tuple[str, ...] = (
    "pNInz6obpgDQGcFmaJgB",  # Adam
    "EXAVITQu4vr4xnSDxMaL",  # Bella
    "ErXwobaYiN019PkySvjV",  # Antoni
    "TxGEqnHWrfWFTfGW9XjX",  # Josh
    "21m00Tcm4TlvDq8ikWAM",  # Rachel
)
# Cap the walk: each rejected voice is a wasted round trip, and a scene of narration should not
# spend 30 seconds discovering the account has nothing usable.
_MAX_VOICE_ATTEMPTS = 6


async def _voice_candidates(client: httpx.AsyncClient, key: str, language: str) -> list[str]:
    """Voice ids to try, best first: the configured one, then free-usable account voices.

    Returns a LIST rather than one id because usability is only knowable by trying: a voice can
    be present on the account and still 402 on synthesis. The caller walks the list.
    """
    out: list[str] = []
    configured = _configured_voice_for(language)
    if configured:
        out.append(configured)
    try:
        resp = await client.get(f"{_API}/voices", headers={"xi-api-key": key})
        resp.raise_for_status()
        voices = resp.json().get("voices") or []
        # Group by category so premade (always free-usable) is tried before anything else.
        for category in _USABLE_CATEGORIES:
            for v in voices:
                vid = str(v.get("voice_id") or "")
                if vid and v.get("category") == category and vid not in out:
                    out.append(vid)
    except Exception as exc:  # noqa: BLE001 - fall through to the hardcoded defaults
        logger.warning("ElevenLabs: could not list voices ({})", str(exc)[:160])
    out += [v for v in _DEFAULT_VOICE_IDS if v not in out]
    return out[:_MAX_VOICE_ATTEMPTS]


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

    blocked: list[str] = []
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        candidates = await _voice_candidates(client, key, lang.code)
        if not candidates:
            raise FatalProviderError("elevenlabs: no voice available on this account")
        for voice_id in candidates:
            resp = await client.post(
                f"{_API}/text-to-speech/{voice_id}",
                headers={"xi-api-key": key, "Content-Type": "application/json"},
                params={"output_format": _OUTPUT_FORMAT},
                json=body,
            )
            if resp.status_code == 402:
                # This specific voice needs a paid plan (library/professional voices do on the
                # free tier). Another voice on the same account may well work, so roll on.
                blocked.append(voice_id)
                logger.info("ElevenLabs: voice {} needs a paid plan; trying the next one", voice_id)
                continue
            if resp.status_code == 429:
                raise RateLimitError(resp.text[:200])
            if 500 <= resp.status_code < 600:
                raise TransientProviderError(f"{resp.status_code}: {resp.text[:120]}")
            if resp.status_code >= 400:
                raise FatalProviderError(f"{resp.status_code}: {resp.text[:200]}")
            return resp.content

    raise FatalProviderError(
        f"402: every available voice requires a paid plan (tried {len(blocked)}). "
        "Pick a default/premade voice on elevenlabs.io and set ELEVENLABS_VOICE_ID to it."
    )


def describe(language: str = "en") -> str:
    """Human-readable engine label for a render note."""
    return f"ElevenLabs ({_model_for(language)})"
