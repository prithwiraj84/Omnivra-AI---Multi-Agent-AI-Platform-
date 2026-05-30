"""Hugging Face provider (image generation) via the Inference API (httpx).

Used by the Image Generation agent (black-forest-labs/FLUX.1-dev). Text completion
returns a stub (this client is image-only); real image generation is exercised in
the Phase-8 media service.
"""
from __future__ import annotations

import httpx

from app.providers._compat import make_stub_response
from app.providers.base import (
    BaseProvider,
    CompletionRequest,
    CompletionResponse,
    FatalProviderError,
    RateLimitError,
    TransientProviderError,
    with_provider_retry,
)


class HuggingFaceProvider(BaseProvider):
    name = "huggingface"

    def __init__(self, *, api_key: str | None, endpoint: str, timeout: float = 120.0) -> None:
        super().__init__(api_key=api_key, timeout=timeout)
        self._endpoint = endpoint

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        # Image-only client; return a stub so the orchestrator never crashes if routed here.
        return make_stub_response(request, self.name)

    @with_provider_retry(max_attempts=4)
    async def generate_image(self, *, prompt: str, model: str = "black-forest-labs/FLUX.1-dev") -> bytes:
        """Generate a PNG via the HF Inference API. Returns raw image bytes."""
        if not self.is_configured:
            raise FatalProviderError("HUGGINGFACE_API_KEY is not configured")
        url = self._endpoint.rstrip("/") + f"/models/{model}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    url, headers={"Authorization": f"Bearer {self._api_key}"}, json={"inputs": prompt}
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
