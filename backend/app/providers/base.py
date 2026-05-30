"""Base provider interface and the shared tenacity retry policy.

Every concrete provider (Google AI Studio, OpenRouter, Groq, Hugging Face)
subclasses :class:`BaseProvider` and decorates its network calls with
:func:`with_provider_retry` so that 429 (rate limit), timeouts, and transient
5xx/connection errors are retried with exponential backoff + jitter, while
other errors (auth, bad request) fail fast.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.config import get_settings
from app.core.logging import logger


class ProviderError(Exception):
    """Base class for provider failures."""


class RateLimitError(ProviderError):
    """HTTP 429 from a provider. Retried with backoff."""


class TransientProviderError(ProviderError):
    """Timeout / 5xx / connection error. Retried with backoff."""


class FatalProviderError(ProviderError):
    """Auth / 4xx (non-429) / malformed request. NOT retried."""


def _is_retryable(exc: BaseException) -> bool:
    """Predicate: should tenacity retry this exception?"""
    if isinstance(exc, (RateLimitError, TransientProviderError)):
        return True
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        return code == 429 or 500 <= code < 600
    return False


def _log_retry(retry_state: Any) -> None:  # tenacity.RetryCallState
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "Provider retry {}/{} after error: {}",
        retry_state.attempt_number,
        retry_state.retry_object.stop.max_attempt_number,
        repr(exc),
    )


def with_provider_retry(
    *, max_attempts: int | None = None, initial: float = 1.0, maximum: float = 30.0
):
    """Decorator factory applying exponential backoff + jitter to a coroutine.

    Retries only on rate-limit / timeout / transient errors (see ``_is_retryable``).
    Auth and malformed-request errors raise immediately. After the final attempt
    the last exception propagates so the LangGraph node can record FAILED.

    ``max_attempts`` defaults to ``settings.provider_max_retries`` (single source of
    truth) when not given; pass an explicit value to override per provider.
    """
    attempts = max_attempts if max_attempts is not None else get_settings().provider_max_retries
    return retry(
        reraise=True,
        stop=stop_after_attempt(attempts),
        wait=wait_exponential_jitter(initial=initial, max=maximum),
        retry=retry_if_exception(_is_retryable),
        before_sleep=_log_retry,
    )


@dataclass(slots=True)
class CompletionRequest:
    """Normalised chat/completion request passed to any text provider."""

    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CompletionResponse:
    """Normalised provider response."""

    text: str
    model: str
    provider: str
    raw: dict[str, Any] = field(default_factory=dict)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class BaseProvider(abc.ABC):
    """Abstract async interface every provider client implements.

    Subclasses set :attr:`name` and implement :meth:`complete`. They MUST wrap
    network calls with :func:`with_provider_retry` and translate provider-native
    errors into ``RateLimitError`` / ``TransientProviderError`` / ``FatalProviderError``.
    """

    name: str = "base"

    def __init__(self, *, api_key: str | None, timeout: float = 60.0) -> None:
        self._api_key = api_key
        self._timeout = timeout

    @property
    def is_configured(self) -> bool:
        """True when an API key is present (drives 'online' dots on the dashboard)."""
        return bool(self._api_key)

    @abc.abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a text completion. Implementations apply the retry decorator."""
        raise NotImplementedError

    async def aclose(self) -> None:
        """Release any underlying HTTP client. Overridden as needed."""
        return None
