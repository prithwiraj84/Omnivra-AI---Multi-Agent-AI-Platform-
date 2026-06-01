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
from app.providers.registry import get_provider_registry
from app.services.artifacts import get_artifact_service
from app.services.usage import record_media_call
from app.workspace_fs.paths import DEFAULT_PROJECT

# All media artifacts live under reports/media so they surface in the Workspace view.
_MEDIA_DIR = "reports/media"
_AGENT_ID = "reel-automation"


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
            return None, "Set GROQ_API_KEY to synthesize real audio via Groq Orpheus TTS."
        clean = (text or "").strip()
        if not clean:
            return None, "No text to synthesize."
        try:
            data = await provider.generate_audio(  # type: ignore[attr-defined]
                text=clean, model=s.groq_tts_model, voice=s.groq_tts_voice, response_format=s.groq_tts_format
            )
            if not data:
                return None, "Groq TTS returned no audio."
            rel = f"{_MEDIA_DIR}/{uuid.uuid4().hex}.{s.groq_tts_format or 'wav'}"
            get_artifact_service(project_id).fm.write_bytes(rel, data, agent_id=_AGENT_ID)
            return rel, f"Voiceover via Groq {s.groq_tts_model} (voice: {s.groq_tts_voice})."
        except Exception as exc:  # noqa: BLE001 - never let TTS break the caller
            logger.warning("Groq TTS failed (continuing without audio): {}", repr(exc))
            # Surface the provider's actual message (e.g. "requires terms acceptance ... console.groq.com")
            # so the silent-render reason is actionable rather than swallowed.
            return None, f"Groq TTS unavailable: {str(exc)[:200]}"

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
