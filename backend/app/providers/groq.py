"""Groq provider (OpenAI-compatible) via httpx. Stubs when unconfigured.

Handles fast text models (QA, SEO, Reel) plus Text-to-Speech via the OpenAI-compatible
``/audio/speech`` endpoint (Orpheus ``canopylabs/orpheus-v1-english`` by default). STT
(Whisper) still lives in the media service.
"""
from __future__ import annotations

import httpx

from app.providers._compat import make_stub_response, openai_chat
from app.providers.base import (
    BaseProvider,
    CompletionRequest,
    CompletionResponse,
    FatalProviderError,
    RateLimitError,
    TransientProviderError,
    with_provider_retry,
)


class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self, *, api_key: str | None, base_url: str, timeout: float = 60.0) -> None:
        super().__init__(api_key=api_key, timeout=timeout)
        self._base_url = base_url

    @with_provider_retry()
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self.is_configured:
            return make_stub_response(request, self.name)
        return await openai_chat(
            base_url=self._base_url,
            api_key=self._api_key or "",
            request=request,
            provider_name=self.name,
            timeout=self._timeout,
        )

    @with_provider_retry(max_attempts=3)
    async def generate_audio(self, *, text: str, model: str, voice: str, response_format: str = "wav") -> bytes:
        """Synthesize speech via Groq's OpenAI-compatible /audio/speech endpoint. Returns audio bytes.

        Used for Orpheus TTS (canopylabs/orpheus-v1-english). A 4xx (e.g. the model not being
        available on the account) raises FatalProviderError so the caller can degrade to silent.
        """
        if not self.is_configured:
            raise FatalProviderError("GROQ_API_KEY is not configured")
        url = self._base_url.rstrip("/") + "/audio/speech"
        payload = {"model": model, "input": text, "voice": voice, "response_format": response_format}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    url, headers={"Authorization": f"Bearer {self._api_key}"}, json=payload
                )
        except httpx.TimeoutException as exc:
            raise TransientProviderError(f"timeout: {exc}") from exc
        except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
            raise TransientProviderError(f"connection: {exc}") from exc
        if resp.status_code == 429:
            raise RateLimitError(resp.text[:200])
        if 500 <= resp.status_code < 600:
            raise TransientProviderError(f"{resp.status_code}: {resp.text[:120]}")
        if resp.status_code >= 400:
            raise FatalProviderError(f"{resp.status_code}: {resp.text[:200]}")
        return resp.content
