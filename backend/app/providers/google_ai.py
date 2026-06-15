"""Google AI Studio (Gemini) provider via the generateContent REST API (httpx).

Used by the CEO/Manager (orchestration) and UI/UX Designer. Stubs when unconfigured.
"""
from __future__ import annotations

from app.providers._compat import make_stub_response, post_json
from app.providers.base import BaseProvider, CompletionRequest, CompletionResponse, with_provider_retry

_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GoogleAIProvider(BaseProvider):
    name = "google_ai"

    def __init__(self, *, api_key: str | None, timeout: float = 60.0) -> None:
        super().__init__(api_key=api_key, timeout=timeout)

    @with_provider_retry()
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self.is_configured:
            return make_stub_response(request, self.name)

        contents = [
            {"role": "model" if m.get("role") == "assistant" else "user", "parts": [{"text": m.get("content", "")}]}
            for m in request.messages
            if m.get("role") != "system"
        ]
        sys_parts = [m.get("content", "") for m in request.messages if m.get("role") == "system"]
        gen_cfg: dict = {"temperature": request.temperature}
        if request.max_tokens:
            gen_cfg["maxOutputTokens"] = request.max_tokens
        body: dict = {"contents": contents, "generationConfig": gen_cfg}
        if sys_parts:
            body["systemInstruction"] = {"parts": [{"text": " ".join(sys_parts)}]}

        async def run(key: str) -> CompletionResponse:
            url = f"{_BASE}/models/{request.model}:generateContent?key={key}"
            data = await post_json(url, headers={"Content-Type": "application/json"}, body=body, timeout=self._timeout)
            candidates = data.get("candidates") or []
            text = ""
            if candidates:
                parts = (candidates[0].get("content") or {}).get("parts") or []
                text = "".join(p.get("text", "") for p in parts)
            usage = data.get("usageMetadata") or {}
            return CompletionResponse(
                text=text,
                model=request.model,
                provider=self.name,
                raw=data,
                prompt_tokens=usage.get("promptTokenCount"),
                completion_tokens=usage.get("candidatesTokenCount"),
            )

        return await self._acall(run)
