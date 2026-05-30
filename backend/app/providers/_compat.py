"""Shared provider helpers: an offline stub completion + httpx HTTP calls with
provider-error mapping. Keeps the concrete providers small and consistent.

Using httpx (already installed) instead of vendor SDKs means the whole provider
layer imports and runs with zero extra dependencies; real calls happen only when
an API key is configured.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.providers.base import (
    CompletionRequest,
    CompletionResponse,
    FatalProviderError,
    RateLimitError,
    TransientProviderError,
)


def make_stub_response(request: CompletionRequest, provider_name: str) -> CompletionResponse:
    """Deterministic offline completion (used when an API key is absent).

    Lets the full orchestration graph run and be tested without network access.
    """
    user = next((m.get("content", "") for m in reversed(request.messages) if m.get("role") == "user"), "")
    snippet = (user[:200] + "…") if len(user) > 200 else user
    text = f"[stub · {provider_name}:{request.model}] {snippet}".strip()
    return CompletionResponse(
        text=text,
        model=request.model,
        provider=provider_name,
        raw={"stub": True},
        prompt_tokens=len(user.split()),
        completion_tokens=len(text.split()),
    )


async def post_json(
    url: str, *, headers: dict[str, str], body: dict[str, Any], timeout: float
) -> dict[str, Any]:
    """POST JSON and return the parsed body, mapping HTTP errors to provider errors.

    429 -> RateLimitError; timeout/5xx/connection -> TransientProviderError (retried);
    other 4xx -> FatalProviderError (not retried).
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
    except httpx.TimeoutException as exc:
        raise TransientProviderError(f"timeout: {exc}") from exc
    except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
        raise TransientProviderError(f"connection: {exc}") from exc

    if resp.status_code == 429:
        raise RateLimitError(resp.text[:300])
    if 500 <= resp.status_code < 600:
        raise TransientProviderError(f"{resp.status_code}: {resp.text[:200]}")
    if resp.status_code >= 400:
        raise FatalProviderError(f"{resp.status_code}: {resp.text[:200]}")
    return resp.json()


async def openai_chat(
    *,
    base_url: str,
    api_key: str,
    request: CompletionRequest,
    provider_name: str,
    extra_headers: dict[str, str] | None = None,
    timeout: float = 60.0,
) -> CompletionResponse:
    """Call an OpenAI-compatible /chat/completions endpoint (OpenRouter, Groq)."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    body: dict[str, Any] = {
        "model": request.model,
        "messages": request.messages,
        "temperature": request.temperature,
    }
    if request.max_tokens:
        body["max_tokens"] = request.max_tokens
    body.update(request.extra)

    data = await post_json(base_url.rstrip("/") + "/chat/completions", headers=headers, body=body, timeout=timeout)
    choices = data.get("choices") or [{}]
    text = (choices[0].get("message") or {}).get("content", "") or ""
    usage = data.get("usage") or {}
    return CompletionResponse(
        text=text,
        model=data.get("model", request.model),
        provider=provider_name,
        raw=data,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
    )
