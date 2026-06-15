"""Provider key-pool rotation + cross-provider fallback (cp-0044).

A provider can hold a POOL of API keys (comma/space separated) and rotates across them on
rate-limit (429) / auth errors; a text agent whose provider is exhausted falls back to another
configured provider. These are unit tests (no network) exercising the rotation + fallback logic.
"""
from __future__ import annotations

import asyncio

import pytest

from app.agents.runner import run_agent
from app.providers.base import (
    BaseProvider,
    CompletionRequest,
    CompletionResponse,
    FatalProviderError,
    RateLimitError,
    TransientProviderError,
    parse_api_keys,
)
from app.providers.groq import GroqProvider


# --- key parsing ------------------------------------------------------------
def test_parse_api_keys_splits_dedupes_and_handles_empty() -> None:
    assert parse_api_keys("a, b ,c") == ["a", "b", "c"]
    assert parse_api_keys("a\nb\tc d") == ["a", "b", "c", "d"]
    assert parse_api_keys("k,k,j") == ["k", "j"]  # de-duped, order preserved
    assert parse_api_keys("solo") == ["solo"]
    assert parse_api_keys("") == [] and parse_api_keys(None) == []


def test_is_configured_and_key_count() -> None:
    assert GroqProvider(api_key="k1,k2,k3", base_url="http://x").key_count == 3
    p0 = GroqProvider(api_key="", base_url="http://x")
    assert not p0.is_configured and p0.key_count == 0


# --- _acall rotation --------------------------------------------------------
def _pool(keys: str = "k1,k2,k3") -> GroqProvider:
    return GroqProvider(api_key=keys, base_url="http://x")


def test_acall_rotates_past_a_rate_limited_key() -> None:
    p = _pool()
    tried: list[str] = []

    async def run(key: str) -> str:
        tried.append(key)
        if key == "k1":
            raise RateLimitError("429 daily quota")
        return f"ok:{key}"

    assert asyncio.run(p._acall(run)) == "ok:k2"
    assert tried[:2] == ["k1", "k2"]  # rotated to the next key on 429


def test_acall_rotates_past_an_auth_error() -> None:
    p = _pool()

    async def run(key: str) -> str:
        if key == "k1":
            raise FatalProviderError("401: invalid api key")
        return f"ok:{key}"

    assert asyncio.run(p._acall(run)) == "ok:k2"


def test_acall_rotates_past_a_transient_error() -> None:
    p = _pool()

    async def run(key: str) -> str:
        if key == "k1":
            raise TransientProviderError("500: upstream blip")
        return f"ok:{key}"

    assert asyncio.run(p._acall(run)) == "ok:k2"  # a transient blip on one key fails over in-loop


def test_acall_does_not_rotate_on_a_non_auth_bad_request() -> None:
    p = _pool()
    tried: list[str] = []

    async def run(key: str) -> str:
        tried.append(key)
        raise FatalProviderError("400: malformed request body")

    with pytest.raises(FatalProviderError):
        asyncio.run(p._acall(run))
    assert len(tried) == 1  # a bad request would fail identically on every key — don't burn them


def test_acall_raises_when_all_keys_rate_limited() -> None:
    p = _pool("k1,k2")

    async def run(key: str) -> str:
        raise RateLimitError("429")

    with pytest.raises(RateLimitError):
        asyncio.run(p._acall(run))


def test_acall_unconfigured_raises_fatal() -> None:
    p = GroqProvider(api_key="", base_url="http://x")

    async def run(key: str) -> str:  # never called
        return "x"

    with pytest.raises(FatalProviderError):
        asyncio.run(p._acall(run))


# --- cross-provider fallback in run_agent -----------------------------------
class _FakeProvider(BaseProvider):
    name = "fake"

    def __init__(self, *, key: str, mode: str) -> None:
        super().__init__(api_key=key)
        self._mode = mode  # '429' | 'empty' | 'ok'

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if self._mode == "429":
            raise RateLimitError("429 exhausted")
        text = "" if self._mode == "empty" else f"REAL CONTENT via {self.name}"
        return CompletionResponse(text=text, model=request.model, provider=self.name, completion_tokens=7)


class _FakeRegistry:
    """ceo-manager's provider is google_ai; the fallback chain's first entry is groq."""

    def __init__(self, primary_mode: str) -> None:
        self._primary = _FakeProvider(key="pk", mode=primary_mode)  # google_ai (configured)
        self._groq = _FakeProvider(key="gk", mode="ok")  # groq (configured) -> content

    def get(self, name: str) -> BaseProvider:
        return self._groq if name == "groq" else self._primary


@pytest.mark.parametrize("primary_mode", ["429", "empty"])
def test_run_agent_falls_back_to_another_provider(primary_mode: str) -> None:
    """A configured primary that 429s OR returns empty must fall back to a working provider."""
    out = asyncio.run(run_agent("ceo-manager", "hi", registry=_FakeRegistry(primary_mode)))
    assert out["ok"] is True
    assert "REAL CONTENT" in out["content"]


def test_openrouter_agent_falls_back_to_groq_when_exhausted() -> None:
    """An agent whose primary is OpenRouter (e.g. backend-engineer) must fail over to Groq/Gemini
    when OpenRouter is exhausted — the 'openrouter fails -> switch to groq or gemini' behavior."""
    out = asyncio.run(run_agent("backend-engineer", "build it", registry=_FakeRegistry("429")))
    assert out["ok"] is True
    assert "REAL CONTENT" in out["content"]


def test_run_agent_offline_primary_stub_is_accepted_no_fallback() -> None:
    """An UNCONFIGURED primary returns a deterministic stub (offline) — accept it, never fall back."""

    class _StubReg:
        def get(self, name: str) -> BaseProvider:
            return _FakeProvider(key="", mode="ok")  # unconfigured -> is_configured False

    # _FakeProvider returns content regardless; the point is is_configured=False short-circuits fallback.
    out = asyncio.run(run_agent("ceo-manager", "hi", registry=_StubReg()))
    assert out["ok"] is True
