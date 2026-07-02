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

from dataclasses import dataclass, field
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


# --- Social publishing connectors (multi-field) --------------------------------------------
# Each connector groups several credential FIELDS. A field's `key` doubles as its SecretsStore
# key AND its Settings/env attribute (they're the same lowercase name), so resolve_provider_key
# works for social fields exactly like it does for LLM keys.


@dataclass(frozen=True, slots=True)
class SocialField:
    key: str  # store key == Settings attr (lowercase); env var is its uppercase
    label: str
    secret: bool = True  # rendered as a password field + masked in status
    required: bool = True  # counts toward the connector's "configured" state
    placeholder: str = ""


@dataclass(frozen=True, slots=True)
class SocialConnector:
    id: str
    label: str
    doc_url: str
    fields: tuple[SocialField, ...]
    publish_supported: bool  # is the REAL publish path wired for this platform yet?
    note: str = ""  # a caveat surfaced in the UI (e.g. Instagram's public-URL requirement)
    kinds: tuple[str, ...] = field(default_factory=tuple)  # e.g. ("reel",) / ("post",)


SOCIAL_CONNECTORS: tuple[SocialConnector, ...] = (
    SocialConnector(
        "youtube", "YouTube", "https://console.cloud.google.com/apis/credentials",
        fields=(
            SocialField("youtube_client_id", "Client ID", secret=False, placeholder="…apps.googleusercontent.com"),
            SocialField("youtube_client_secret", "Client secret"),
            SocialField("youtube_refresh_token", "Refresh token"),
        ),
        publish_supported=True, kinds=("reel",),
        note="Reels upload as PRIVATE — flip to Public on YouTube after review.",
    ),
    SocialConnector(
        "linkedin", "LinkedIn", "https://www.linkedin.com/developers/apps",
        fields=(SocialField("linkedin_access_token", "Access token", placeholder="OAuth2 token with w_member_social"),),
        publish_supported=True, kinds=("post",),
    ),
    SocialConnector(
        "facebook", "Facebook Page", "https://developers.facebook.com/apps",
        fields=(
            SocialField("facebook_page_id", "Page ID", secret=False, placeholder="numeric page id"),
            SocialField("facebook_page_token", "Page access token"),
        ),
        publish_supported=True, kinds=("post",),
    ),
    SocialConnector(
        "instagram", "Instagram", "https://developers.facebook.com/docs/instagram-api",
        fields=(
            SocialField("instagram_user_id", "IG Business account ID", secret=False, placeholder="numeric ig user id"),
            SocialField("instagram_access_token", "Access token"),
        ),
        publish_supported=True, kinds=("reel",),
        note="Requires an IG Business/Creator account + Supabase Storage configured (the reel is hosted at a temporary URL Instagram fetches).",
    ),
    SocialConnector(
        "twitter", "X (Twitter)", "https://developer.twitter.com/en/portal/dashboard",
        fields=(
            SocialField("twitter_api_key", "API key"),
            SocialField("twitter_api_secret", "API secret"),
            SocialField("twitter_access_token", "Access token"),
            SocialField("twitter_access_secret", "Access token secret"),
        ),
        publish_supported=True, kinds=("post",),
        note="Posting needs OAuth 1.0a user-context keys (the read-only bearer token can't post).",
    ),
)

_CONNECTOR_BY_ID: dict[str, SocialConnector] = {c.id: c for c in SOCIAL_CONNECTORS}
_SOCIAL_FIELD_KEYS: frozenset[str] = frozenset(f.key for c in SOCIAL_CONNECTORS for f in c.fields)


def is_known_provider(provider: str) -> bool:
    return provider in _BY_ID


def is_known_connector(connector_id: str) -> bool:
    return connector_id in _CONNECTOR_BY_ID


def connector_field_keys(connector_id: str) -> tuple[str, ...]:
    c = _CONNECTOR_BY_ID.get(connector_id)
    return tuple(f.key for f in c.fields) if c else ()


def _settings_attr(key: str) -> str | None:
    """The Settings attribute a stored-key `key` falls back to (env), or None if unknown."""
    spec = _BY_ID.get(key)
    if spec:
        return spec.env_attr
    if key in _SOCIAL_FIELD_KEYS:
        return key  # social field key == its settings attr
    return None


def _env_key(provider: str) -> str | None:
    attr = _settings_attr(provider)
    if not attr:
        return None
    value = getattr(get_settings(), attr, None)
    return value or None


def resolve_provider_key(provider: str) -> str | None:
    """The effective key for a provider/field: stored overrides env; None when neither is set."""
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


def connector_configured(connector_id: str) -> bool:
    """True when every REQUIRED field of a social connector resolves (stored or env)."""
    c = _CONNECTOR_BY_ID.get(connector_id)
    if not c:
        return False
    return all(resolve_provider_key(f.key) is not None for f in c.fields if f.required)


def social_connector_status() -> list[dict[str, object]]:
    """Per-connector status for GET /system/social-connectors. NEVER includes raw values."""
    store = get_secrets_store()
    stored = store.stored_providers()
    out: list[dict[str, object]] = []
    for c in SOCIAL_CONNECTORS:
        fields: list[dict[str, object]] = []
        configured = True
        for f in c.fields:
            env_set = _env_key(f.key) is not None
            stored_set = f.key in stored
            source: KeySource = "stored" if stored_set else ("env" if env_set else "none")
            if f.required and source == "none":
                configured = False
            fields.append(
                {
                    "key": f.key,
                    "label": f.label,
                    "envVar": f.key.upper(),
                    "secret": f.secret,
                    "required": f.required,
                    "placeholder": f.placeholder,
                    "envSet": env_set,
                    "storedSet": stored_set,
                    "source": source,
                    "masked": mask_key(store.get(f.key)) if stored_set else None,
                }
            )
        out.append(
            {
                "id": c.id,
                "label": c.label,
                "docUrl": c.doc_url,
                "publishSupported": c.publish_supported,
                "note": c.note,
                "kinds": list(c.kinds),
                "configured": configured,
                "fields": fields,
            }
        )
    return out
