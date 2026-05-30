"""Drift guard: keep ``supabase/seed.sql`` in lockstep with the agent registry.

The Python registry (``app.agents.registry.AGENT_REGISTRY``) and the SQL seed
are two hand-maintained copies of the same roster. If one is edited without the
other, the dashboard and the database fall out of sync. This test fails loudly
when the SQL seed no longer mentions an agent id or a model string that the
registry declares.

Naming convention note: the registry uses kebab-case ids (``ceo-manager``) while
the SQL ``agents.key`` column uses snake_case (``ceo_manager``). They are the
same identifier in two conventions, so id matching normalizes hyphens to
underscores. Model strings are vendor-exact and are matched verbatim.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.agents.registry import AGENT_REGISTRY

SEED_SQL_PATH = Path(__file__).resolve().parents[2] / "supabase" / "seed.sql"


def _load_seed_text() -> str:
    if not SEED_SQL_PATH.exists():
        pytest.skip(f"seed.sql not found at {SEED_SQL_PATH}; skipping drift guard")
    return SEED_SQL_PATH.read_text(encoding="utf-8")


def test_registry_has_full_roster() -> None:
    assert len(AGENT_REGISTRY) == 23


def test_every_agent_id_is_present_in_seed() -> None:
    seed = _load_seed_text()
    missing = [
        agent_id
        for agent_id in AGENT_REGISTRY
        # kebab-case registry id vs snake_case SQL key: normalize before matching
        if agent_id.replace("-", "_") not in seed
    ]
    assert not missing, f"agent ids in registry but absent from seed.sql: {missing}"


def test_every_model_string_is_present_in_seed() -> None:
    seed = _load_seed_text()
    models = sorted({spec.model for spec in AGENT_REGISTRY.values()})
    missing = [model for model in models if model not in seed]
    assert not missing, f"models in registry but absent from seed.sql: {missing}"
