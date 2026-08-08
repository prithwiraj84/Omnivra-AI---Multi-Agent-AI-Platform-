"""Hugging Face MMS text-to-speech — the FREE fallback for non-English narration.

Groq's speech models are English-only, so a Hindi script has nowhere to go if the user hasn't
connected ElevenLabs. Meta's MMS-TTS models are served on the same Hugging Face endpoint the
image agent already uses, so a user with only a (free) HF token still gets genuinely Hindi
audio. It is noticeably more robotic than ElevenLabs — that trade is stated in the render note
rather than hidden, so "why does this sound synthetic?" has an answer in the UI.

Sits LAST in the chain: it only ever runs when the good engine is absent or failed.
"""
from __future__ import annotations

import io
import re
import wave

from app.core.logging import logger
from app.providers.base import FatalProviderError, TransientProviderError
from app.providers.registry import get_provider_registry

# Meta MMS-TTS, one VITS checkpoint per language. Only languages we can actually route.
_MODELS: dict[str, str] = {
    "hi": "facebook/mms-tts-hin",
}
# MMS is a sentence-level model — long inputs get truncated rather than rejected, which would
# silently cut narration off mid-word. Split first, then splice the audio back together.
_MAX_CHARS = 320
# Devanagari danda + Latin terminators, so both scripts split on real sentence ends.
_SENTENCE_SPLIT = re.compile(r"(?<=[।?!.])\s+")


def supports(language: str) -> bool:
    """True when this engine has a model for ``language``."""
    return language in _MODELS


def is_configured(language: str = "hi") -> bool:
    """True when a HF key is available AND we have a model for this language."""
    if not supports(language):
        return False
    return bool(getattr(get_provider_registry().get("huggingface"), "is_configured", False))


def audio_ext(data: bytes) -> str:
    """The file extension matching ``data``'s magic bytes.

    The endpoint's audio container varies by model/serving stack, and writing .wav bytes to a
    .mp3 path is exactly the kind of mismatch that makes ffmpeg refuse the clip later.
    """
    if data[:4] == b"RIFF":
        return "wav"
    if data[:4] == b"fLaC":
        return "flac"
    if data[:4] == b"OggS":
        return "ogg"
    if data[:3] == b"ID3" or data[:2] == b"\xff\xfb":
        return "mp3"
    return "wav"


def _chunks(text: str) -> list[str]:
    """Split ``text`` into <=_MAX_CHARS pieces on sentence boundaries (never mid-word)."""
    text = (text or "").strip()
    if len(text) <= _MAX_CHARS:
        return [text] if text else []
    out: list[str] = []
    current = ""
    for sentence in _SENTENCE_SPLIT.split(text):
        # A single sentence longer than the cap still has to go somewhere; send it whole and
        # let the model do its best rather than slicing a word in half.
        if current and len(current) + len(sentence) + 1 > _MAX_CHARS:
            out.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        out.append(current)
    return out


def _splice_wav(parts: list[bytes]) -> bytes:
    """Concatenate WAV clips into one. Raises if they aren't all compatible WAV."""
    out = io.BytesIO()
    writer: wave.Wave_write | None = None
    try:
        for part in parts:
            with wave.open(io.BytesIO(part), "rb") as reader:
                if writer is None:
                    writer = wave.open(out, "wb")
                    writer.setparams(reader.getparams())
                writer.writeframes(reader.readframes(reader.getnframes()))
    finally:
        if writer is not None:
            writer.close()
    return out.getvalue()


async def synthesize(text: str, *, language: str = "hi") -> bytes:
    """Synthesize ``text`` in ``language`` via HF MMS-TTS. Raises so the caller can degrade."""
    model = _MODELS.get(language)
    if not model:
        raise FatalProviderError(f"hf: no MMS voice for language {language!r}")
    provider = get_provider_registry().get("huggingface")
    if not getattr(provider, "is_configured", False):
        raise FatalProviderError("hf: HUGGINGFACE_API_KEY is not configured")

    parts = _chunks(text)
    if not parts:
        raise FatalProviderError("hf: nothing to synthesize")

    audio = [await provider.generate_audio(text=part, model=model) for part in parts]  # type: ignore[attr-defined]
    audio = [a for a in audio if a]
    if not audio:
        raise TransientProviderError("hf: MMS returned no audio")
    if len(audio) == 1:
        return audio[0]
    # Multi-chunk only splices cleanly for WAV. Rather than emit a truncated clip, fail and let
    # the caller report honestly that Hindi narration needs ElevenLabs.
    if not all(a[:4] == b"RIFF" for a in audio):
        raise TransientProviderError("hf: MMS returned non-WAV audio that cannot be joined")
    try:
        return _splice_wav(audio)
    except Exception as exc:  # noqa: BLE001 - mismatched sample rates etc.
        logger.warning("HF MMS: could not splice {} clips ({})", len(audio), str(exc)[:160])
        raise TransientProviderError(f"hf: could not join MMS audio ({str(exc)[:120]})") from exc


def describe(language: str = "hi") -> str:
    """Human-readable engine label for a render note."""
    return f"Hugging Face {_MODELS.get(language, 'MMS-TTS')}"
