"""Application configuration via pydantic-settings.

Reads from environment variables and backend/.env. Access through the cached
``get_settings()`` so the file is parsed once per process.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env  (this file lives at backend/app/core/config.py)
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Strongly-typed runtime settings."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App / runtime ---
    app_name: str = "Omnivra AI Company OS"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    log_json: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    workspace_root: str = "../workspace"

    # --- Providers ---
    google_ai_studio_api_key: str | None = None

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "https://omnivra.local"
    openrouter_app_name: str = "Omnivra AI Company OS"

    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    # Groq Text-to-Speech (OpenAI-compatible /audio/speech). Orpheus by default; override
    # to a PlayAI voice (e.g. model "playai-tts", voice "Fritz-PlayAI") if your account
    # doesn't have Orpheus access.
    groq_tts_model: str = "canopylabs/orpheus-v1-english"
    # Groq's Orpheus voices are: autumn, diana, hannah, austin, daniel, troy
    # (NOT the canopylabs upstream names like 'tara'). PlayAI uses e.g. 'Fritz-PlayAI'.
    groq_tts_voice: str = "autumn"
    groq_tts_format: str = "wav"

    huggingface_api_key: str | None = None
    # HF retired api-inference.huggingface.co; serverless inference now routes through
    # router.huggingface.co/<provider>. hf-inference serves FLUX.1-schnell for image gen.
    huggingface_inference_endpoint: str = "https://router.huggingface.co/hf-inference"

    # --- Social pipeline (cp-0016): media source + platform publishers ---
    # All optional; unset -> the reel/post pipeline runs in stub mode (no real upload).
    pexels_api_key: str | None = None  # stock B-roll for reels (Pexels Video API)
    # YouTube uploads use OAuth2 (refresh token), not an API key (cp-0020).
    youtube_client_id: str | None = None
    youtube_client_secret: str | None = None
    youtube_refresh_token: str | None = None
    instagram_access_token: str | None = None  # Instagram Graph API (reels)
    facebook_page_token: str | None = None  # Facebook Page (posts)
    linkedin_access_token: str | None = None  # LinkedIn (posts)
    twitter_bearer_token: str | None = None  # Twitter / X (posts)

    # --- Supabase ---
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_db_password: str | None = None
    supabase_db_url: str | None = None
    supabase_storage_bucket: str = "omnivra-artifacts"

    # --- Redis / Upstash ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Orchestration safety ---
    max_recursion: int = 3
    provider_timeout_seconds: float = 60.0
    # Per-call attempts before giving up on a provider. Kept low (2) because the key POOL already
    # rotates across all of a provider's keys within a single attempt, and run_agent then fails over
    # to another provider — so a dead/exhausted provider switches over PROMPTLY instead of burning
    # several backoff retries on it first.
    provider_max_retries: int = 2

    # --- Security / Auth ---
    api_secret_key: str = "change-me-in-prod"
    # Auth is OPT-IN: dev runs open (auth_enabled=False). Set AUTH_ENABLED=true in prod.
    auth_enabled: bool = False
    admin_username: str = "admin"
    admin_password: str = "omnivra"
    token_ttl_seconds: int = 86400
    # Hardening (opt-in to avoid throttling local/dev + tests).
    security_headers_enabled: bool = True
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 240

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins parsed from the comma-separated env string."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def workspace_path(self) -> Path:
        """Absolute, resolved path to the AI artifact sandbox."""
        p = Path(self.workspace_root)
        if not p.is_absolute():
            p = (_BACKEND_DIR / p).resolve()
        return p


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached Settings instance."""
    return Settings()
