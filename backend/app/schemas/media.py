"""Media service schemas (image / TTS / STT). camelCase on the wire.

These DTOs describe the stub-safe media service results: a generated (or
placeholder) artifact path plus a ``stub`` flag and a human-readable ``note``
explaining what to configure for the real provider call.
"""
from __future__ import annotations

from app.schemas.dashboard import CamelModel


class ImageRequest(CamelModel):
    prompt: str


class TTSRequest(CamelModel):
    text: str


class STTRequest(CamelModel):
    filename: str | None = None


class MediaResult(CamelModel):
    """Result of an image-generation or text-to-speech call."""

    path: str | None = None
    stub: bool
    note: str


class TranscriptionResult(CamelModel):
    """Result of a speech-to-text (transcription) call."""

    text: str
    stub: bool
    note: str
