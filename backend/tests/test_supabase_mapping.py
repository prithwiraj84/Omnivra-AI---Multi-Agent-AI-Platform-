"""SupabaseRepository row->Agent mapping must match supabase/schema.sql column names.

Guards the cp-0024 fix: the query/mapping previously used provider_kind / model_key /
kind / model / id, but the schema uses providers.key / models.model_id / is_system /
agents.key. This maps a representative joined row (no DB/client needed) and asserts
the DTO is correct, so a schema<->repo drift fails the suite instead of silently
falling back to seed at runtime.
"""
from __future__ import annotations

from app.db.repositories.supabase_repo import SupabaseRepository


def test_row_to_agent_matches_schema_columns() -> None:
    repo = SupabaseRepository.__new__(SupabaseRepository)  # _row_to_agent needs no client
    row = {
        "key": "ceo_manager",
        "name": "CEO / Manager",
        "status": "online",
        "is_system": False,
        "departments": {"name": "Executive"},
        "providers": {"key": "google_ai_studio"},
        "models": {"model_id": "gemini-2.5-flash"},
    }
    agent = repo._row_to_agent(row)

    assert agent.id == "ceo-manager"  # underscores -> hyphens (registry/frontend convention)
    assert agent.name == "CEO / Manager"
    assert agent.department == "Executive"
    assert agent.provider == "google_ai"  # provider_kind enum 'google_ai_studio' -> 'google_ai'
    assert agent.model == "gemini-2.5-flash"
    assert agent.kind == "text"  # is_system False
    assert agent.status == "online"
    assert agent.provider_label and agent.model_label  # label maps resolved


def test_row_to_agent_media_is_not_system_ops() -> None:
    # Media agents are is_system=true in the schema but must map to kind='media'
    # (their own group), NOT 'system' — else they'd render under "System Operations".
    repo = SupabaseRepository.__new__(SupabaseRepository)
    row = {
        "key": "image_generation",
        "name": "Image Generation",
        "status": "online",
        "is_system": True,
        "departments": {"name": "Media"},
        "providers": {"key": "huggingface"},
        "models": {"model_id": "black-forest-labs/FLUX.1-dev"},
    }
    agent = repo._row_to_agent(row)
    assert agent.kind == "media"  # not 'system'
    assert agent.provider == "huggingface"
    assert agent.model == "black-forest-labs/FLUX.1-dev"


def test_row_to_agent_system_ops_stays_system() -> None:
    repo = SupabaseRepository.__new__(SupabaseRepository)
    row = {
        "key": "task_classifier",
        "name": "Task Classifier",
        "status": "online",
        "is_system": True,
        "departments": {"name": "System Ops"},
        "providers": {"key": "openrouter"},
        "models": {"model_id": "liquid/lfm-2.5-1.2b-thinking:free"},
    }
    assert repo._row_to_agent(row).kind == "system"
