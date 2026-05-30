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

PROVIDER_NAMES = ("google_ai", "openrouter", "groq", "huggingface")


class ProviderRegistry:
    """Lazily constructs and caches provider clients from Settings."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[str, BaseProvider] = {}

    def get(self, name: str) -> BaseProvider:
        if name in self._cache:
            return self._cache[name]
        client = self._build(name)
        self._cache[name] = client
        return client

    def _build(self, name: str) -> BaseProvider:
        s = self._settings
        if name == "google_ai":
            return GoogleAIProvider(
                api_key=s.google_ai_studio_api_key, timeout=s.provider_timeout_seconds
            )
        if name == "openrouter":
            return OpenRouterProvider(
                api_key=s.openrouter_api_key,
                base_url=s.openrouter_base_url,
                site_url=s.openrouter_site_url,
                app_name=s.openrouter_app_name,
                timeout=s.provider_timeout_seconds,
            )
        if name == "groq":
            return GroqProvider(
                api_key=s.groq_api_key,
                base_url=s.groq_base_url,
                timeout=s.provider_timeout_seconds,
            )
        if name == "huggingface":
            return HuggingFaceProvider(
                api_key=s.huggingface_api_key,
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
