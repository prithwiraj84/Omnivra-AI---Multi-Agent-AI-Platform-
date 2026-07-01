"""Provider-key catalog + resolution + masking — the single source of truth for in-app keys.

`resolve_provider_key(name)` is the ONE precedence rule every consumer (the provider registry,
Pexels, etc.) calls so they always agree:

    stored (workspace/.state/provider_keys.json)  →  env (backend/.env via Settings)  →  None

Stored OVERRIDES env by design: if the admin never enters a UI key, behavior is exactly as
today (env is used verbatim, so existing tests are unaffected); the only new behavior is that a
key the admin explicitly typed and saved wins — the obvious "what I put in the box runs" model.
Clearing the stored key falls back to env. The active source is reported to the UI so it stays
honest about where the running key came from.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.config import get_settings
from app.services.secrets_store import get_secrets_store

KeySource = Literal["stored", "env", "none"]


@dataclass(frozen=True, slots=True)
class ProviderKeySpec:
    """One configurable provider key."""

    id: str
    label: str
    category: Literal["llm", "media"]
    env_attr: str  # the Settings attribute / env var (uppercased) this maps to
    doc_url: str

    @property
    def env_var(self) -> str:
        return self.env_attr.upper()


# Order drives the UI. The four LLM providers back the agent runtime; Pexels feeds reel b-roll.
PROVIDER_KEY_CATALOG: tuple[ProviderKeySpec, ...] = (
    ProviderKeySpec("google_ai", "Google AI Studio", "llm", "google_ai_studio_api_key", "https://aistudio.google.com/app/apikey"),
    ProviderKeySpec("openrouter", "OpenRouter", "llm", "openrouter_api_key", "https://openrouter.ai/keys"),
    ProviderKeySpec("groq", "Groq", "llm", "groq_api_key", "https://console.groq.com/keys"),
    ProviderKeySpec("huggingface", "Hugging Face", "llm", "huggingface_api_key", "https://huggingface.co/settings/tokens"),
    ProviderKeySpec("pexels", "Pexels", "media", "pexels_api_key", "https://www.pexels.com/api/new/"),
)

_BY_ID: dict[str, ProviderKeySpec] = {spec.id: spec for spec in PROVIDER_KEY_CATALOG}


def is_known_provider(provider: str) -> bool:
    return provider in _BY_ID


def _env_key(provider: str) -> str | None:
    spec = _BY_ID.get(provider)
    if not spec:
        return None
    value = getattr(get_settings(), spec.env_attr, None)
    return value or None


def resolve_provider_key(provider: str) -> str | None:
    """The effective key for a provider: stored overrides env; None when neither is set."""
    stored = get_secrets_store().get(provider)
    if stored:
        return stored
    return _env_key(provider)


def key_source(provider: str) -> KeySource:
    """Where the ACTIVE key comes from ('stored' | 'env' | 'none')."""
    if get_secrets_store().get(provider):
        return "stored"
    if _env_key(provider):
        return "env"
    return "none"


def mask_key(raw: str | None) -> str | None:
    """Redact a key for display. Never returns more than a short prefix + last 4 chars.

    None -> None; short keys are fully bulleted; otherwise 'abcd…wxyz'.
    """
    if not raw:
        return None
    s = raw.strip()
    if len(s) <= 8:
        return "•" * len(s)
    return f"{s[:4]}…{s[-4:]}"


def provider_key_status() -> list[dict[str, object]]:
    """Per-provider status for GET /system/provider-keys. NEVER includes raw key values."""
    store = get_secrets_store()
    stored = store.stored_providers()
    out: list[dict[str, object]] = []
    for spec in PROVIDER_KEY_CATALOG:
        env_set = _env_key(spec.id) is not None
        stored_set = spec.id in stored
        source: KeySource = "stored" if stored_set else ("env" if env_set else "none")
        out.append(
            {
                "id": spec.id,
                "label": spec.label,
                "category": spec.category,
                "envVar": spec.env_var,
                "docUrl": spec.doc_url,
                "envSet": env_set,
                "storedSet": stored_set,
                "source": source,
                "configured": source != "none",
                # Only the STORED key is ever surfaced (masked) so the admin can recognize what
                # they saved; env keys are never echoed back, masked or otherwise.
                "masked": mask_key(store.get(spec.id)) if stored_set else None,
            }
        )
    return out
