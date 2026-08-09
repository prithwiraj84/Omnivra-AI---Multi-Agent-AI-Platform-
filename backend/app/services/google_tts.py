"""Google Gemini text-to-speech — the FREE multilingual narration path.

This is the engine that makes a non-English reel possible without a paid account. Groq's
speech models are English-only, and Hugging Face's serverless tier no longer hosts ANY
text-to-speech model (`facebook/mms-tts-hin` and friends now report "Model not supported by
provider hf-inference"), so Gemini TTS is the only free engine that actually speaks Hindi —
and it uses the Google AI Studio key most installs already have for the LLM agents.

Two details worth knowing:
  * The API returns RAW PCM (16-bit LE, usually 24 kHz mono), NOT a container. We wrap it in a
    WAV header ourselves — ffmpeg/moviepy will not read the bare samples.
  * The model accepts a natural-language STYLE instruction in the same prompt as the text. It
    is interpreted, not read aloud (measured: adding the instruction made the clip shorter, not
    longer), which is the cheapest available lever against "the voice sounds robotic".
"""
from __future__ import annotations

import base64
import io
import re
import wave

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
from app.services.languages import get_language
from app.services.provider_keys import resolve_provider_key

_API = "https://generativelanguage.googleapis.com/v1beta/models"
AUDIO_EXT = "wav"
_TIMEOUT = 180.0  # a full scene of narration, generated off the request path

# Tried in order; accounts differ in which preview models they can reach, so a 404 on the
# newest one must roll on to the next rather than muting the reel.
_MODELS: tuple[str, ...] = (
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-flash-preview-tts",
)
# Prebuilt voices are global (not per-account), so a default here always resolves.
_DEFAULT_VOICE = "Kore"

# Delivered as a style instruction, not as words to speak.
_STYLE = (
    "Read the following aloud as a warm, energetic social-media narrator. "
    "Natural conversational pace, clear articulation, no rushing, no robotic monotone. "
    "Read ONLY the text itself:\n\n"
)

# The response mime looks like "audio/L16;codec=pcm;rate=24000" or
# "audio/l16; rate=24000; channels=1" — shapes differ per model, so parse rather than assume.
_RATE_RE = re.compile(r"rate=(\d+)", re.IGNORECASE)
_CHANNELS_RE = re.compile(r"channels=(\d+)", re.IGNORECASE)


def is_configured() -> bool:
    return bool(resolve_provider_key("google_ai"))


def _voice_for(language: str) -> str:
    """The prebuilt voice for ``language``: a per-language override, else the general one."""
    s = get_settings()
    per_language = {"hi": s.google_tts_voice_hi}.get(get_language(language).code)
    return ((per_language or "").strip()) or ((s.google_tts_voice or "").strip()) or _DEFAULT_VOICE


def _models() -> list[str]:
    """The configured model first, then the known-good fallbacks, de-duplicated."""
    configured = (get_settings().google_tts_model or "").strip()
    out = [configured] if configured else []
    out += [m for m in _MODELS if m != configured]
    return out


def _pcm_to_wav(pcm: bytes, mime: str) -> bytes:
    """Wrap raw 16-bit PCM in a WAV container, honouring the rate/channels the API reported."""
    rate = int(_RATE_RE.search(mime).group(1)) if _RATE_RE.search(mime) else 24_000
    channels = int(_CHANNELS_RE.search(mime).group(1)) if _CHANNELS_RE.search(mime) else 1
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)  # L16 == signed 16-bit little-endian
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def _extract_audio(payload: dict) -> tuple[bytes, str] | None:
    """Pull (pcm_bytes, mime) out of a generateContent response, or None if it carried no audio."""
    for candidate in payload.get("candidates") or []:
        for part in (candidate.get("content") or {}).get("parts") or []:
            inline = part.get("inlineData") or part.get("inline_data")
            if not inline or not inline.get("data"):
                continue
            mime = inline.get("mimeType") or inline.get("mime_type") or ""
            try:
                return base64.b64decode(inline["data"]), mime
            except Exception as exc:  # noqa: BLE001 - malformed payload -> treat as no audio
                logger.warning("Gemini TTS: undecodable audio payload ({})", str(exc)[:120])
                return None
    return None


@with_provider_retry(max_attempts=2)
async def synthesize(text: str, *, language: str = "en") -> bytes:
    """Synthesize ``text`` to WAV bytes in ``language``.

    Raises on failure so the caller can fall through to the next engine in the chain.
    """
    keys = parse_api_keys(resolve_provider_key("google_ai"))
    if not keys:
        raise FatalProviderError("google: no API key configured")

    body = {
        "contents": [{"parts": [{"text": _STYLE + text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": _voice_for(language)}}},
        },
    }

    last: Exception | None = None
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Model outer, key inner: a model this project can't reach fails the same way for every
        # key in the pool, whereas a rate limit is per-key — so rotating keys first is what
        # actually buys another shot at the SAME model.
        for model in _models():
            for key in keys:
                try:
                    resp = await client.post(f"{_API}/{model}:generateContent", params={"key": key}, json=body)
                except httpx.TimeoutException as exc:
                    raise TransientProviderError(f"google: timeout ({exc})") from exc
                except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                    raise TransientProviderError(f"google: connection ({exc})") from exc

                if resp.status_code == 429:
                    last = RateLimitError(f"google {model}: {resp.text[:160]}")
                    continue  # this key is throttled; the next one may not be
                if 500 <= resp.status_code < 600:
                    last = TransientProviderError(f"google {model}: {resp.status_code}")
                    continue
                if resp.status_code >= 400:
                    # 404/400 usually means this account can't reach this preview model.
                    last = FatalProviderError(f"google {model}: {resp.status_code}: {resp.text[:160]}")
                    break  # try the next MODEL, not the next key
                audio = _extract_audio(resp.json())
                if audio is None:
                    last = TransientProviderError(f"google {model}: response carried no audio")
                    continue
                pcm, mime = audio
                if not pcm:
                    last = TransientProviderError(f"google {model}: empty audio")
                    continue
                return _pcm_to_wav(pcm, mime)

    raise last or FatalProviderError("google: no TTS model available on this account")


def describe(language: str = "en") -> str:
    """Human-readable engine label for a render note."""
    return f"Google Gemini TTS (voice: {_voice_for(language)})"
