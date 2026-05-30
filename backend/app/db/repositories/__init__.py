"""Repository factory and re-exports.

:func:`get_repository` selects the data source at runtime: a
:class:`SupabaseRepository` when a Supabase client is available, otherwise the
default :class:`SeedRepository`. The chosen instance is cached for the process.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.db.client import get_supabase_client
from app.db.repositories.base import DashboardRepository
from app.db.repositories.seed_repo import SeedRepository
from app.db.repositories.supabase_repo import SupabaseRepository

__all__ = [
    "DashboardRepository",
    "SeedRepository",
    "SupabaseRepository",
    "get_repository",
]


@lru_cache(maxsize=1)
def _cached_repository() -> DashboardRepository:
    client = get_supabase_client()
    if client is not None:
        return SupabaseRepository(client)
    return SeedRepository()


def get_repository(settings: Settings | None = None) -> DashboardRepository:
    """Return the process-wide dashboard repository.

    Uses Supabase when :func:`get_supabase_client` is configured, else the seed
    repository. ``settings`` is accepted for API symmetry / explicit callers;
    the selection itself reads the cached client/settings.
    """
    _ = settings or get_settings()
    return _cached_repository()
