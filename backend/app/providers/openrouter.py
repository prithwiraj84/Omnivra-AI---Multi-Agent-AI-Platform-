"""OpenRouter provider (OpenAI-compatible) via httpx. Stubs when unconfigured.

Most engineering, security, marketing, documentation, recovery, and system-ops
agents route here.
"""
from __future__ import annotations

from app.providers._compat import make_stub_response, openai_chat
from app.providers.base import BaseProvider, CompletionRequest, CompletionResponse, with_provider_retry


class OpenRouterProvider(BaseProvider):
    name = "openrouter"

    def __init__(
        self, *, api_key: str | None, base_url: str, site_url: str, app_name: str, timeout: float = 60.0
    ) -> None:
        super().__init__(api_key=api_key, timeout=timeout)
        self._base_url = base_url
        # OpenRouter attribution headers (ranking + usage dashboards).
        self._headers = {"HTTP-Referer": site_url, "X-Title": app_name}

    @with_provider_retry()
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self.is_configured:
            return make_stub_response(request, self.name)
        return await openai_chat(
            base_url=self._base_url,
            api_key=self._api_key or "",
            request=request,
            provider_name=self.name,
            extra_headers=self._headers,
            timeout=self._timeout,
        )
