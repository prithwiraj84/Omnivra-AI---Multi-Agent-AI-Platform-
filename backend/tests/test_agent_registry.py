"""The agent roster is the dashboard's source of truth — guard its shape."""
from __future__ import annotations

from app.agents.registry import (
    AGENT_REGISTRY,
    AgentSpec,
    Department,
    agents_by_department,
    get_agent,
    list_agents,
)

KNOWN_PROVIDERS = {"google_ai", "openrouter", "groq", "huggingface"}


def test_registry_is_populated() -> None:
    assert len(AGENT_REGISTRY) >= 20
    assert len(list_agents()) == len(AGENT_REGISTRY)


def test_ceo_is_gemini() -> None:
    ceo = get_agent("ceo-manager")
    assert isinstance(ceo, AgentSpec)
    assert ceo.department is Department.EXECUTIVE
    assert ceo.provider == "google_ai"
    assert ceo.model == "gemini-2.5-flash"


def test_every_agent_has_a_known_provider_and_model() -> None:
    for spec in AGENT_REGISTRY.values():
        assert spec.provider in KNOWN_PROVIDERS, f"{spec.id} → unknown provider {spec.provider}"
        assert spec.model, f"{spec.id} has no model"
        assert spec.id == spec.id.lower(), "ids must be kebab-case lowercase"


def test_ids_are_unique_and_match_keys() -> None:
    for key, spec in AGENT_REGISTRY.items():
        assert key == spec.id


def test_grouping_covers_all_agents() -> None:
    grouped = agents_by_department()
    assert sum(len(v) for v in grouped.values()) == len(AGENT_REGISTRY)
    # Every represented department is a valid enum value.
    valid = {d.value for d in Department}
    assert set(grouped).issubset(valid)
