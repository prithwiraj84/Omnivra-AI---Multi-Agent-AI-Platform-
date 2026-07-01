"""Provider registry: resolve a provider name to a configured client singleton.

The agent runtime looks up ``AgentSpec.provider`` (e.g. 'openrouter') here to get
the right :class:`BaseProvider`. Clients are created lazily and cached per process.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.providers.base import BaseProvider
from app.providers.google_ai import GoogleAIProvider
from app.providers.groq import GroqProvider
from app.providers.huggingface import HuggingFaceProvider
from app.providers.openrouter import OpenRouterProvider
from app.services.provider_keys import resolve_provider_key
from app.services.secrets_store import get_secrets_store

PROVIDER_NAMES = ("google_ai", "openrouter", "groq", "huggingface")


class ProviderRegistry:
    """Lazily constructs and caches provider clients from Settings.

    Secret keys come from ``resolve_provider_key`` (stored overrides env), NOT straight from
    Settings, so a key the admin saves in the UI is honored. Cached clients are refreshed in
    place when the SecretsStore epoch advances, so a newly-saved/cleared key takes effect on the
    very next call — no process restart, no reconnect.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[str, BaseProvider] = {}
        self._epoch: dict[str, int] = {}

    def get(self, name: str) -> BaseProvider:
        epoch = get_secrets_store().epoch
        client = self._cache.get(name)
        if client is None:
            client = self._build(name)
            self._cache[name] = client
            self._epoch[name] = epoch
            return client
        if self._epoch.get(name) != epoch:
            # A key was saved/cleared since we built this client — refresh its pool in place.
            client.set_keys(resolve_provider_key(name))
            self._epoch[name] = epoch
        return client

    def _build(self, name: str) -> BaseProvider:
        s = self._settings
        if name == "google_ai":
            return GoogleAIProvider(
                api_key=resolve_provider_key("google_ai"), timeout=s.provider_timeout_seconds
            )
        if name == "openrouter":
            return OpenRouterProvider(
                api_key=resolve_provider_key("openrouter"),
                base_url=s.openrouter_base_url,
                site_url=s.openrouter_site_url,
                app_name=s.openrouter_app_name,
                timeout=s.provider_timeout_seconds,
            )
        if name == "groq":
            return GroqProvider(
                api_key=resolve_provider_key("groq"),
                base_url=s.groq_base_url,
                timeout=s.provider_timeout_seconds,
            )
        if name == "huggingface":
            return HuggingFaceProvider(
                api_key=resolve_provider_key("huggingface"),
                endpoint=s.huggingface_inference_endpoint,
            )
        raise KeyError(f"Unknown provider: {name!r}. Expected one of {PROVIDER_NAMES}")

    def status(self) -> dict[str, bool]:
        """Map provider name -> configured? (drives provider 'online' dots)."""
        return {n: self.get(n).is_configured for n in PROVIDER_NAMES}

    async def aclose(self) -> None:
        for client in self._cache.values():
            await client.aclose()


@lru_cache(maxsize=1)
def get_provider_registry() -> ProviderRegistry:
    """Process-wide provider registry built from the cached settings."""
    return ProviderRegistry(get_settings())
