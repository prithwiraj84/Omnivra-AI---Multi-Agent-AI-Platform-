"""MediaService — stub-safe image / TTS / STT, always writing inside the workspace.

Every method degrades gracefully: when the underlying provider key is missing it
writes a small placeholder artifact (so something still shows up in the Workspace
view) and returns ``stub=True`` with a note explaining what to configure. Writes
reuse :class:`ArtifactService`'s path-jailed FileManager, so media artifacts can
never escape the workspace sandbox (the WORKSPACE RULE).

Real provider calls:
  - Image: Hugging Face Inference API (black-forest-labs/FLUX.1-dev) -> PNG bytes.
  - STT:   Groq Whisper (whisper-large-v3-turbo) — needs an audio upload + key.
  - TTS:   Groq Orpheus — needs a key (not yet wired to a real synth call).
"""
from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

from app.core.logging import logger
from app.providers.registry import get_provider_registry
from app.services.artifacts import get_artifact_service
from app.workspace_fs.paths import DEFAULT_PROJECT

# All media artifacts live under reports/media so they surface in the Workspace view.
_MEDIA_DIR = "reports/media"
_AGENT_ID = "reel-automation"


class MediaService:
    """Generate (or stub) media artifacts inside the workspace sandbox."""

    async def generate_image(self, prompt: str, project_id: str = DEFAULT_PROJECT) -> dict[str, Any]:
        """Generate a PNG from ``prompt`` via Hugging Face, or write a stub placeholder.

        Returns ``{"path", "stub", "note"}``. Never raises to the caller: any
        provider/IO failure falls back to a placeholder artifact + ``stub=True``.
        """
        fm = get_artifact_service(project_id).fm
        provider = get_provider_registry().get("huggingface")

        if getattr(provider, "is_configured", False):
            try:
                data = await provider.generate_image(prompt=prompt)  # type: ignore[attr-defined]
                rel = f"{_MEDIA_DIR}/{uuid.uuid4().hex}.png"
                fm.write_bytes(rel, data, agent_id=_AGENT_ID)
                return {"path": rel, "stub": False, "note": "Image generated via Hugging Face FLUX.1-dev."}
            except Exception as exc:  # noqa: BLE001 - never let media IO break the caller
                logger.warning("Image generation failed, writing stub: {}", repr(exc))

        rel = self._write_placeholder(
            fm,
            suffix="txt",
            body=(
                "[stub image]\n"
                f"prompt: {prompt}\n"
                "Set HUGGINGFACE_API_KEY to generate a real PNG via black-forest-labs/FLUX.1-dev."
            ),
        )
        return {
            "path": rel,
            "stub": True,
            "note": "Set HUGGINGFACE_API_KEY to generate real images (black-forest-labs/FLUX.1-dev).",
        }

    async def transcribe(self, filename: str | None) -> dict[str, Any]:
        """Transcribe an audio file (STT). Stubs when the Groq key is unset."""
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

    async def generate_voiceover(self, text: str, project_id: str = DEFAULT_PROJECT) -> str | None:
        """Synthesize a real voiceover (Orpheus via HF) into the workspace; rel path or None.

        Returns None (no audio) when no HF key is configured or synthesis fails — the
        reel renderer then composes a silent video. Used by the reel render engine.
        """
        provider = get_provider_registry().get("huggingface")
        if not getattr(provider, "is_configured", False):
            return None
        try:
            data = await provider.generate_audio(text=text)  # type: ignore[attr-defined]
            rel = f"{_MEDIA_DIR}/{uuid.uuid4().hex}.wav"
            get_artifact_service(project_id).fm.write_bytes(rel, data, agent_id=_AGENT_ID)
            return rel
        except Exception as exc:  # noqa: BLE001 - never let TTS break the render
            logger.warning("Voiceover synthesis failed (continuing silent): {}", repr(exc))
            return None

    async def synthesize(self, text: str, project_id: str = DEFAULT_PROJECT) -> dict[str, Any]:
        """Synthesize speech from ``text`` (TTS). Stubs when the Groq key is unset."""
        fm = get_artifact_service(project_id).fm
        rel = self._write_placeholder(
            fm,
            suffix="txt",
            body=f"[stub tts]\ntext: {text}\nSet GROQ_API_KEY to synthesize real audio via Groq Orpheus.",
        )
        return {
            "path": rel,
            "stub": True,
            "note": "Set GROQ_API_KEY to synthesize real audio via Groq Orpheus TTS.",
        }

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
