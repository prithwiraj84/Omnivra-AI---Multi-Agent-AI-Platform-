"""Media routes: image generation, text-to-speech, speech-to-text.

All endpoints are stub-safe — without provider keys they still return a 200 with
``stub=True`` and (for image/TTS) write a placeholder artifact into the workspace,
so the Workspace view always has something to show.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_project_id
from app.schemas import (
    ImageRequest,
    MediaResult,
    STTRequest,
    TranscriptionResult,
    TTSRequest,
)
from app.services.media import get_media_service

router = APIRouter(tags=["media"])


@router.post("/image", response_model=MediaResult)
async def generate_image(req: ImageRequest, project_id: str = Depends(get_project_id)) -> MediaResult:
    """Generate an image from a prompt (or a stub placeholder artifact) in the active project."""
    return MediaResult(**await get_media_service().generate_image(req.prompt, project_id))


@router.post("/tts", response_model=MediaResult)
async def text_to_speech(req: TTSRequest, project_id: str = Depends(get_project_id)) -> MediaResult:
    """Synthesize speech from text (or a stub placeholder artifact) in the active project."""
    return MediaResult(**await get_media_service().synthesize(req.text, project_id))


@router.post("/stt", response_model=TranscriptionResult)
async def speech_to_text(req: STTRequest) -> TranscriptionResult:
    """Transcribe an audio file by name (stub when no Groq key is configured)."""
    return TranscriptionResult(**await get_media_service().transcribe(req.filename))
