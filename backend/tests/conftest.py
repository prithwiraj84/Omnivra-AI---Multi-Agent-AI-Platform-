"""Shared pytest fixtures for the Omnivra backend.

The workspace root is redirected to a temp directory *before* the app is imported,
so the test suite never writes into the real ``workspace/`` sandbox and ``get_settings()``
(which is ``lru_cache``d) picks up the override the first time it is constructed.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

# Redirect the artifact sandbox to a throwaway dir before anything imports app.*
_TMP_WORKSPACE = tempfile.mkdtemp(prefix="omnivra-test-ws-")
os.environ.setdefault("WORKSPACE_ROOT", _TMP_WORKSPACE)
os.environ.setdefault("APP_ENV", "test")

# Keep the suite hermetic + offline: neutralize ANY real credentials in backend/.env
# so tests never hit the network (deterministic + fast). Without this, real provider
# keys make agents do live LLM calls with tenacity retries -> the suite hangs.
for _k in (
    # data / cache
    "SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_DB_URL", "SUPABASE_DB_PASSWORD",
    # per-user isolation OFF by default -> single-admin open mode (current_user == admin)
    "SUPABASE_JWT_SECRET",
    # LLM / media providers (unset -> deterministic stub responses)
    "GOOGLE_AI_STUDIO_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY", "HUGGINGFACE_API_KEY",
    # social pipeline (unset -> stub publish / no b-roll / no voiceover)
    "PEXELS_API_KEY", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN",
    "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_USER_ID", "FACEBOOK_PAGE_TOKEN", "FACEBOOK_PAGE_ID",
    "LINKEDIN_ACCESS_TOKEN", "TWITTER_BEARER_TOKEN",
    "TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET",
):
    os.environ[_k] = ""

# Force the documented auth defaults so a customized backend/.env (real ADMIN_USERNAME /
# ADMIN_PASSWORD / AUTH_ENABLED) can't break the hermetic auth tests — os.environ overrides .env.
os.environ["AUTH_ENABLED"] = "false"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "omnivra"

# Force STUB reel rendering in tests so the suite is fast + deterministic even when
# the optional MoviePy engine is installed locally (a real encode takes ~tens of sec).
os.environ["OMNIVRA_DISABLE_RENDER"] = "1"

# Disable the dashboard payload cache so tests see live data on every call (the cache is a prod
# optimization; with the session-scoped client it would otherwise return a stale snapshot).
os.environ["DASHBOARD_CACHE_TTL"] = "0"


@pytest.fixture(scope="session")
def client() -> Iterator["object"]:
    """A FastAPI TestClient with lifespan (startup/shutdown) actually run."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
