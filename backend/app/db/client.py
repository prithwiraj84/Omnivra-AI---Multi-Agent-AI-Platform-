"""Supabase client factory.

The data layer is Supabase-optional: with zero Supabase configuration the app
runs entirely on the seed repository. :func:`get_supabase_client` therefore
returns ``None`` unless both the project URL and the service-role key are set,
and imports the ``supabase`` SDK lazily so the package imports cleanly even when
the dependency is not installed.
"""
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import Settings, get_settings
from app.core.logging import logger

if TYPE_CHECKING:  # pragma: no cover - typing only
    from supabase import Client


def supabase_configured(settings: Settings) -> bool:
    """True when both the Supabase URL and service-role key are present."""
    return bool(settings.supabase_url and settings.supabase_service_role_key)


@lru_cache(maxsize=1)
def get_supabase_client() -> "Client | None":
    """Return a process-wide Supabase client, or ``None`` when unconfigured.

    Constructs ``supabase.create_client(url, service_role_key)`` only when both
    values are set. Any import/construction failure is logged and treated as
    "not configured" so the app falls back to the seed repository.
    """
    settings = get_settings()
    if not supabase_configured(settings):
        return None

    try:
        from supabase import create_client  # lazy: SDK may be absent

        client = create_client(
            settings.supabase_url,  # type: ignore[arg-type]  # guarded above
            settings.supabase_service_role_key,  # type: ignore[arg-type]
        )
    except Exception as exc:  # noqa: BLE001 - never let DB wiring crash startup
        logger.warning("Supabase client unavailable, using seed data: {}", exc)
        return None

    logger.info("Supabase client initialised for {}", settings.supabase_url)
    return client
