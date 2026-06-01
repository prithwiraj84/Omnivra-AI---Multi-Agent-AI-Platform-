"""Supabase-backed repository.

Reads agents live from Supabase (``agents`` joined to ``departments``,
``providers`` and ``models``) and maps each row to :class:`schemas.Agent`,
reusing the same label/accent maps as :mod:`app.data.seed` so live and seed
output agree field-for-field. For everything not yet persisted as live
operational rows (stats, workflows, task execution, activity, approvals, system
health, usage, media, achievements) it delegates to a composed
:class:`~app.db.repositories.seed_repo.SeedRepository`.

Every Supabase call is wrapped so a misconfigured or unreachable database never
500s the dashboard — it logs and falls back to the seed repository instead.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.logging import logger
from app.data.seed import DEPARTMENT_ACCENT, MODEL_LABEL, PROVIDER_LABEL
from app.db.repositories.seed_repo import SeedRepository
from app.schemas.dashboard import (
    Agent,
    ActivityItem,
    ApprovalItem,
    DashboardPayload,
    HealthMetric,
    WorkflowItem,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from supabase import Client

# DB provider_kind enum -> registry provider key. The Supabase enum spells the
# Google provider 'google_ai_studio'; the registry/seed maps use 'google_ai'.
# Every other provider key matches the enum value verbatim.
_PROVIDER_KIND_TO_KEY = {"google_ai_studio": "google_ai"}


class SupabaseRepository:
    """Repository that reads agents from Supabase and seeds the rest."""

    def __init__(self, client: "Client") -> None:
        self._client = client
        self._seed = SeedRepository()
        self._warned = False  # log the seed-fallback warning once, not every poll

    # --- agents (live) -----------------------------------------------------
    def list_agents(self) -> list[Agent]:
        """All agents from Supabase; seed fallback on any error."""
        try:
            rows = self._fetch_agent_rows()
        except Exception as exc:  # noqa: BLE001 - never break the dashboard
            if not self._warned:
                logger.warning("Supabase list_agents failed, using seed (run supabase/schema.sql + seed.sql to enable live rows): {}", exc)
                self._warned = True
            else:
                logger.debug("Supabase list_agents still failing, using seed: {}", exc)
            return self._seed.list_agents()

        if not rows:
            logger.info("Supabase returned no agents, using seed agents")
            return self._seed.list_agents()

        return [self._row_to_agent(row) for row in rows]

    def get_agent(self, agent_id: str) -> Agent | None:
        for agent in self.list_agents():
            if agent.id == agent_id:
                return agent
        return None

    # --- aggregate (live agents + seeded rest) -----------------------------
    def get_dashboard(self) -> DashboardPayload:
        payload = self._seed.get_dashboard()
        try:
            agents = self.list_agents()
        except Exception as exc:  # noqa: BLE001 - defensive; list_agents already guards
            logger.warning("Supabase get_dashboard agents failed, using seed: {}", exc)
            return payload

        primary = [a for a in agents if a.kind != "system"]
        system = [a for a in agents if a.kind == "system"]
        # Rebuild the payload with live agents but seeded operational data.
        return payload.model_copy(update={"agents": primary, "system_ops": system})

    # --- delegated (not yet live) ------------------------------------------
    def list_workflows(self) -> list[WorkflowItem]:
        return self._seed.list_workflows()

    def list_approvals(self) -> list[ApprovalItem]:
        return self._seed.list_approvals()

    def list_activity(self) -> list[ActivityItem]:
        return self._seed.list_activity()

    def get_system_health(self) -> list[HealthMetric]:
        return self._seed.get_system_health()

    # --- internals ---------------------------------------------------------
    def _fetch_agent_rows(self) -> list[dict[str, Any]]:
        """Select agents joined to departments, providers and models.

        Column names match supabase/schema.sql: agents(key, name, status, is_system),
        providers(key = the provider_kind enum), models(model_id = the model string).
        """
        response = (
            self._client.table("agents")
            .select(
                "key, name, status, is_system, sort_order,"
                " departments(name),"
                " providers(key),"
                " models(model_id)"
            )
            .order("sort_order")
            .execute()
        )
        return list(response.data or [])

    def _row_to_agent(self, row: dict[str, Any]) -> Agent:
        """Map one joined DB row (schema.sql shape) to a :class:`schemas.Agent` DTO."""
        department = _nested(row, "departments", "name") or ""
        provider_kind = _nested(row, "providers", "key") or ""
        provider = _PROVIDER_KIND_TO_KEY.get(provider_kind, provider_kind)
        model = _nested(row, "models", "model_id") or ""
        # DB keys use underscores (ceo_manager); the registry/frontend use hyphens.
        key = str(row.get("key", ""))
        # is_system marks BOTH Media + System-Ops agents in the schema; distinguish by
        # department so Media (Whisper/Orpheus/FLUX) shows in the agent grid — not under
        # the "System Operations (LFM 1.2B)" row. Mirrors the registry's AgentKind.
        kind = "media" if department == "Media" else ("system" if row.get("is_system") else "text")

        return Agent(
            id=key.replace("_", "-"),
            name=str(row.get("name", "")),
            department=department,
            accent=DEPARTMENT_ACCENT.get(department, "cyan"),
            provider=provider,
            provider_label=PROVIDER_LABEL.get(provider, provider),
            model=model,
            model_label=MODEL_LABEL.get(model, model),
            kind=kind,
            status=str(row.get("status", "online")),
        )


def _nested(row: dict[str, Any], relation: str, field: str) -> str | None:
    """Read ``row[relation][field]``, tolerating list-shaped or missing joins.

    Supabase returns embedded one-to-one joins as either an object or a
    single-element list depending on the relationship cardinality.
    """
    value = row.get(relation)
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, dict):
        result = value.get(field)
        return None if result is None else str(result)
    return None
