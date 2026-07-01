"""Base provider interface and the shared tenacity retry policy.

Every concrete provider (Google AI Studio, OpenRouter, Groq, Hugging Face)
subclasses :class:`BaseProvider` and decorates its network calls with
:func:`with_provider_retry` so that 429 (rate limit), timeouts, and transient
5xx/connection errors are retried with exponential backoff + jitter, while
other errors (auth, bad request) fail fast.
"""
from __future__ import annotations

import abc
import re
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.config import get_settings
from app.core.logging import logger

# How long a key that just hit a limit / was rejected is de-prioritized before the pool
# will prefer it again. A rate-limited key recovers quickly (per-minute windows); a key the
# provider rejected as invalid (auth) is parked far longer so the pool stops wasting calls on it.
_RATE_COOLDOWN_SEC = 45.0
_AUTH_COOLDOWN_SEC = 1800.0

T = TypeVar("T")


def parse_api_keys(raw: str | None) -> list[str]:
    """Split a configured key string into a POOL of keys (comma / whitespace / newline separated).

    Lets a single env var hold several keys, e.g. ``GROQ_API_KEY=key1,key2,key3`` — the provider
    then rotates across them on rate limits. A lone key (no separators) yields a one-element pool;
    empty/None yields an empty pool (provider reports unconfigured -> offline stub)."""
    if not raw:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for part in re.split(r"[,\s]+", raw.strip()):
        k = part.strip()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _is_auth_error(exc: BaseException) -> bool:
    """True when a FatalProviderError looks like a bad/unauthorized KEY (so the pool rotates past it),
    vs a genuine bad-request that every key would hit identically."""
    msg = str(exc).lower()
    if msg.startswith("401") or msg.startswith("403"):
        return True
    return ("api key not valid" in msg) or ("invalid api key" in msg) or ("unauthorized" in msg) or ("api_key_invalid" in msg)


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
        # A POOL of keys (api_key may be comma/space separated). The provider rotates across them
        # on rate limits, so several free-tier keys behave like one larger quota with failover.
        self._keys: list[str] = parse_api_keys(api_key)
        self._timeout = timeout
        self._cursor = 0  # round-robin start, so load spreads across the pool
        self._cooldowns: dict[str, float] = {}  # key -> monotonic time until it's preferred again
        self._klock = threading.Lock()  # guards the (tiny, sync) cursor/cooldown mutations only

    @property
    def is_configured(self) -> bool:
        """True when at least one API key is present (drives 'online' dots on the dashboard)."""
        return bool(self._keys)

    def set_keys(self, api_key: str | None) -> None:
        """Replace the key pool in place (used when the admin saves/clears a key in the UI).

        Cheap and connection-safe: the provider reads ``self._keys`` fresh on the next call,
        so no client rebuild/reconnect is needed. Resets the rotation cursor + cooldowns since
        the pool changed."""
        with self._klock:
            self._keys = parse_api_keys(api_key)
            self._cursor = 0
            self._cooldowns.clear()

    @property
    def _api_key(self) -> str | None:
        """The first key in the pool — backward-compatible accessor for single-key call sites."""
        return self._keys[0] if self._keys else None

    @property
    def key_count(self) -> int:
        """Number of keys in the pool (for diagnostics / dashboards)."""
        return len(self._keys)

    def _attempt_order(self) -> list[str]:
        """The KEYS to try this call: round-robin, preferring keys NOT in cooldown, but always
        returning at least one so a call is still attempted when every key is cooling.

        Returns a stable SNAPSHOT of key strings (taken under the lock), not indices — so a
        concurrent ``set_keys`` that swaps ``self._keys`` mid-call can never shift an index out
        from under the caller (was an IndexError race). An empty pool yields ``[]``."""
        now = time.monotonic()
        with self._klock:
            keys = list(self._keys)  # snapshot; immune to a later self._keys rebind
            n = len(keys)
            if n == 0:
                return []
            order = [keys[(self._cursor + i) % n] for i in range(n)]
            self._cursor = (self._cursor + 1) % n
            fresh = [k for k in order if self._cooldowns.get(k, 0.0) <= now]
        return fresh or order

    def _cool(self, key: str, seconds: float) -> None:
        with self._klock:
            self._cooldowns[key] = time.monotonic() + seconds

    async def _acall(self, run: Callable[[str], Awaitable[T]]) -> T:
        """Run ``run(key)`` against the key pool, ROTATING to the next key on a rate-limit (429) or
        an auth/bad-key error; return the first success. Raises the last error if every key fails
        (the ``with_provider_retry`` decorator then applies backoff and may rotate again). A genuine
        non-auth bad-request raises immediately (rotating keys could not help)."""
        attempts = self._attempt_order()  # stable snapshot of keys to try
        if not attempts:
            raise FatalProviderError(f"{self.name}: no API key configured")
        total = len(attempts)
        last: BaseException | None = None
        for i, key in enumerate(attempts):
            try:
                return await run(key)
            except RateLimitError as exc:
                last = exc
                self._cool(key, _RATE_COOLDOWN_SEC)
                logger.warning("{}: API key #{}/{} rate-limited; rotating to the next key", self.name, i + 1, total)
            except TransientProviderError as exc:
                # timeout / 5xx / connection blip — not the key's fault (no cooldown), but try the next
                # key in-loop too (a healthy key may succeed immediately); if all fail, propagate so the
                # with_provider_retry decorator applies backoff.
                last = exc
                logger.warning("{}: API key #{}/{} transient error; trying the next key", self.name, i + 1, total)
            except FatalProviderError as exc:
                if _is_auth_error(exc):
                    last = exc
                    self._cool(key, _AUTH_COOLDOWN_SEC)
                    logger.warning("{}: API key #{}/{} rejected (auth); rotating", self.name, i + 1, total)
                    continue
                raise  # non-auth fatal (e.g. bad request) — every key would fail identically
        raise last if last is not None else FatalProviderError(f"{self.name}: all API keys failed")

    @abc.abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a text completion. Implementations apply the retry decorator."""
        raise NotImplementedError

    async def aclose(self) -> None:
        """Release any underlying HTTP client. Overridden as needed."""
        return None
