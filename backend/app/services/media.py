"""MediaService — stub-safe image / TTS / STT, always writing inside the workspace.

Every method degrades gracefully: when the underlying provider key is missing it
writes a small placeholder artifact (so something still shows up in the Workspace
view) and returns ``stub=True`` with a note explaining what to configure. Writes
reuse :class:`ArtifactService`'s path-jailed FileManager, so media artifacts can
never escape the workspace sandbox (the WORKSPACE RULE).

Real provider calls:
  - Image: Hugging Face Inference router (black-forest-labs/FLUX.1-schnell) -> image bytes.
  - STT:   Groq Whisper (whisper-large-v3-turbo) — needs an audio upload + key.
  - TTS:   Groq Orpheus (canopylabs/orpheus-v1-english) via the OpenAI-compatible
           /audio/speech endpoint -> a real .wav. Degrades to silent / a stub placeholder
           when GROQ_API_KEY is unset or the model isn't available on the account.
"""
from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.logging import logger
from app.providers.base import FatalProviderError
from app.providers.registry import get_provider_registry
from app.services.artifacts import get_artifact_service
from app.services.usage import record_media_call
from app.workspace_fs.paths import DEFAULT_PROJECT

# All media artifacts live under reports/media so they surface in the Workspace view.
_MEDIA_DIR = "reports/media"
_AGENT_ID = "reel-automation"


# --- TTS model fallback ----------------------------------------------------------------------
# Groq accounts differ in which speech models they can use: a model may be retired, gated behind
# a one-time terms acceptance, or simply absent from the plan. A voice ALSO only works with its
# own model family, so a fallback must swap model AND voice together. We try the configured pair
# first, then these, so a reel gets a voiceover instead of rendering mute.
_TTS_FALLBACK_PAIRS: tuple[tuple[str, str], ...] = (
    ("playai-tts", "Fritz-PlayAI"),
    ("canopylabs/orpheus-v1-english", "autumn"),
)


def _tts_candidates(model: str | None, voice: str | None) -> list[tuple[str, str]]:
    """The configured (model, voice) first, then the known-good fallbacks, de-duplicated."""
    out: list[tuple[str, str]] = []
    if model and voice:
        out.append((model, voice))
    for pair in _TTS_FALLBACK_PAIRS:
        if pair[0] not in {m for m, _ in out}:
            out.append(pair)
    return out


class MediaService:
    """Generate (or stub) media artifacts inside the workspace sandbox."""

    async def generate_image(self, prompt: str, project_id: str = DEFAULT_PROJECT) -> dict[str, Any]:
        """Generate an image (JPEG/PNG) from ``prompt`` via Hugging Face, or write a stub placeholder.

        Returns ``{"path", "stub", "note"}``. Never raises to the caller: any
        provider/IO failure falls back to a placeholder artifact + ``stub=True``.
        """
        record_media_call("image")
        fm = get_artifact_service(project_id).fm
        provider = get_provider_registry().get("huggingface")

        if getattr(provider, "is_configured", False):
            try:
                data = await provider.generate_image(prompt=prompt)  # type: ignore[attr-defined]
                # FLUX.1-schnell returns JPEG; pick the extension by magic bytes so the media
                # endpoint serves the right Content-Type.
                ext = "jpg" if data[:3] == b"\xff\xd8\xff" else "png"
                rel = f"{_MEDIA_DIR}/{uuid.uuid4().hex}.{ext}"
                fm.write_bytes(rel, data, agent_id=_AGENT_ID)
                return {"path": rel, "stub": False, "note": "Image generated via Hugging Face FLUX.1-schnell."}
            except Exception as exc:  # noqa: BLE001 - never let media IO break the caller
                logger.warning("Image generation failed, writing stub: {}", repr(exc))

        rel = self._write_placeholder(
            fm,
            suffix="txt",
            body=(
                "[stub image]\n"
                f"prompt: {prompt}\n"
                "Set HUGGINGFACE_API_KEY to generate a real image via black-forest-labs/FLUX.1-schnell."
            ),
        )
        return {
            "path": rel,
            "stub": True,
            "note": "Set HUGGINGFACE_API_KEY to generate real images (black-forest-labs/FLUX.1-schnell).",
        }

    async def transcribe(self, filename: str | None) -> dict[str, Any]:
        """Transcribe an audio file (STT). Stubs when the Groq key is unset."""
        record_media_call("stt")
        provider = get_provider_registry().get("groq")
        if getattr(provider, "is_configured", False):
            # A real call needs the uploaded audio bytes, not just a name; until the
            # upload path is wired we still return a stub but flag it as such.
            return {
                "text": "[stub transcription]",
                "stub": True,
                "note": (
                    "Groq Whisper STT (whisper-large-v3-turbo) needs an uploaded audio file; "
                    "filename alone is not enough."
                ),
            }
        return {
            "text": "[stub transcription]",
            "stub": True,
            "note": (
                "Set GROQ_API_KEY and upload audio to enable real Groq Whisper STT "
                "(whisper-large-v3-turbo)."
            ),
        }

    async def voiceover_with_note(self, text: str, project_id: str = DEFAULT_PROJECT) -> tuple[str | None, str]:
        """Synthesize a reel voiceover; return ``(rel_path | None, note)``.

        The note explains a miss (no key / terms-acceptance / model access / provider error)
        so the render pipeline can surface WHY a reel ended up silent instead of swallowing it.
        """
        record_media_call("tts")
        return await self._tts(text, project_id)

    async def generate_voiceover(self, text: str, project_id: str = DEFAULT_PROJECT) -> str | None:
        """Synthesize a real voiceover (Groq Orpheus) into the workspace; rel path or None.

        Returns None (no audio) when GROQ_API_KEY is unset or synthesis fails — the reel
        renderer then composes a silent video. Used by the reel render engine.
        """
        rel, _note = await self.voiceover_with_note(text, project_id)
        return rel

    async def synthesize(self, text: str, project_id: str = DEFAULT_PROJECT) -> dict[str, Any]:
        """Synthesize speech from ``text`` (TTS) via Groq Orpheus; stub placeholder if unavailable."""
        record_media_call("tts")
        rel, note = await self._tts(text, project_id)
        if rel:
            return {"path": rel, "stub": False, "note": note}
        fm = get_artifact_service(project_id).fm
        placeholder = self._write_placeholder(fm, suffix="txt", body=f"[stub tts]\ntext: {text}\n{note}")
        return {"path": placeholder, "stub": True, "note": note}

    async def _tts(self, text: str, project_id: str) -> tuple[str | None, str]:
        """Core TTS: synthesize ``text`` via Groq Orpheus into a workspace audio file.

        Returns ``(rel_path | None, note)``. Never raises: an unconfigured key, empty text,
        or any provider/model error returns ``(None, note)`` so callers degrade gracefully
        (silent video / stub placeholder). The model/voice/format come from Settings, so the
        user can switch to a PlayAI voice without code changes.
        """
        s = get_settings()
        provider = get_provider_registry().get("groq")
        if not getattr(provider, "is_configured", False):
            return None, "Set GROQ_API_KEY to synthesize real audio via Groq TTS."
        clean = (text or "").strip()
        if not clean:
            return None, "No text to synthesize."

        fmt = s.groq_tts_format or "wav"
        failures: list[str] = []
        for model, voice in _tts_candidates(s.groq_tts_model, s.groq_tts_voice):
            try:
                data = await provider.generate_audio(  # type: ignore[attr-defined]
                    text=clean, model=model, voice=voice, response_format=fmt
                )
            except FatalProviderError as exc:
                # 4xx: this model/voice isn't usable on the account (retired, terms not accepted,
                # no access, or a voice that belongs to a different model family). Try the next
                # candidate instead of going silent — that's the difference between a working
                # voiceover and a mute reel.
                failures.append(f"{model}: {str(exc)[:120]}")
                logger.warning("Groq TTS model {} rejected ({}); trying the next candidate", model, str(exc)[:120])
                continue
            except Exception as exc:  # noqa: BLE001 - transient/network: stop, report honestly
                logger.warning("Groq TTS failed (continuing without audio): {}", repr(exc))
                return None, f"Groq TTS unavailable: {str(exc)[:200]}"
            if not data:
                failures.append(f"{model}: returned no audio")
                continue
            rel = f"{_MEDIA_DIR}/{uuid.uuid4().hex}.{fmt}"
            get_artifact_service(project_id).fm.write_bytes(rel, data, agent_id=_AGENT_ID)
            note = f"Voiceover via Groq {model} (voice: {voice})."
            if model != s.groq_tts_model:
                note += f" Fell back from {s.groq_tts_model}, which this account can't use."
            return rel, note

        return None, (
            "Groq TTS unavailable — no usable voice model. Tried: "
            + "; ".join(failures)[:300]
            + ". Set GROQ_TTS_MODEL/GROQ_TTS_VOICE to a model your account has, or accept the "
            "model terms at console.groq.com."
        )

    @staticmethod
    def _write_placeholder(fm: Any, *, suffix: str, body: str) -> str | None:
        """Write a small placeholder artifact under reports/media; return its rel path."""
        rel = f"{_MEDIA_DIR}/{uuid.uuid4().hex}.{suffix}"
        try:
            fm.write_text(rel, body, agent_id=_AGENT_ID)
            return rel
        except Exception as exc:  # noqa: BLE001 - never raise to the caller
            logger.warning("Placeholder media write failed: {}", repr(exc))
            return None


@lru_cache(maxsize=1)
def get_media_service() -> MediaService:
    """Process-wide MediaService singleton."""
    return MediaService()
