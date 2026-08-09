"""System routes: health metrics, provider status, runtime info, and in-app API-key config."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app import __version__, schemas
from app.agents.registry import AGENT_REGISTRY
from app.api.deps import MEDIA_TOKEN_TTL_SECONDS, current_user, get_repo, per_user_mode
from app.core.config import get_settings
from app.core.security import create_token
from app.db.client import supabase_configured
from app.db.repositories import DashboardRepository
from app.providers.registry import get_provider_registry
from app.services.provider_keys import (
    connector_field_keys,
    is_known_connector,
    is_known_provider,
    provider_key_status,
    social_connector_status,
)
from app.services.secrets_store import get_secrets_store

router = APIRouter(tags=["system"])


@router.get("/health", response_model=list[schemas.HealthMetric])
def get_system_health(repo: DashboardRepository = Depends(get_repo)) -> list[schemas.HealthMetric]:
    """Return the system-health metrics."""
    return repo.get_system_health()


@router.get("/providers")
def providers(_current: str = Depends(current_user)) -> dict[str, bool]:
    """Provider name -> configured? for THIS user (drives the Integrations status dots)."""
    return get_provider_registry().status()


@router.get("/checkpoints")
def checkpoints() -> list[dict[str, object]]:
    """List committed build/recovery checkpoints (workspace/.state/checkpoints/*.json).

    Powers the Recovery view — the cp-NNNN lineage the Recovery Agent resumes from.
    """
    import json
    from pathlib import Path

    base = Path(get_settings().workspace_path) / ".state" / "checkpoints"
    out: list[dict[str, object]] = []
    if base.exists():
        for path in sorted(base.glob("cp-*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            out.append(
                {
                    "id": data.get("id", path.stem),
                    "phase": data.get("phase"),
                    "phaseTitle": data.get("phase_title", ""),
                    "status": data.get("status", ""),
                    "createdAt": data.get("created_at", ""),
                    "parent": data.get("parent"),
                }
            )
    return out


# --- In-app provider API-key configuration (Integrations → API keys) -----------------------
# Lets the admin set/clear LLM & media provider keys from the website when they aren't in
# backend/.env. Keys are PER USER and stored durably (Supabase when configured, else a
# gitignored workspace file) and used at call time. Responses NEVER contain raw key values —
# only a masked hint of a stored key.


class ProviderKeyUpdate(BaseModel):
    """Body for setting a provider key."""

    value: str = Field(..., min_length=1, max_length=4096)


def _provider_or_404(provider_id: str) -> None:
    if not is_known_provider(provider_id):
        raise HTTPException(status_code=404, detail=f"Unknown provider {provider_id!r}")


def _single_status(provider_id: str, owner: str) -> dict[str, object]:
    for row in provider_key_status(owner):
        if row["id"] == provider_id:
            return row
    raise HTTPException(status_code=404, detail=f"Unknown provider {provider_id!r}")


@router.get("/provider-keys")
def list_provider_keys(current: str = Depends(current_user)) -> list[dict[str, object]]:
    """This user's per-provider key status (env/stored/none + masked). No raw secrets returned."""
    return provider_key_status(current)


@router.put("/provider-keys/{provider_id}")
def set_provider_key(
    provider_id: str,
    body: ProviderKeyUpdate,
    current: str = Depends(current_user),
) -> dict[str, object]:
    """Store (or replace) THIS USER's provider key. Used on their very next call."""
    _provider_or_404(provider_id)
    try:
        get_secrets_store().set(current, provider_id, body.value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _single_status(provider_id, current)


@router.delete("/provider-keys/{provider_id}")
def clear_provider_key(
    provider_id: str,
    current: str = Depends(current_user),
) -> dict[str, object]:
    """Remove THIS USER's stored provider key (falls back to the env key, if any)."""
    _provider_or_404(provider_id)
    get_secrets_store().clear(current, provider_id)
    return _single_status(provider_id, current)


# --- Social publishing connectors (multi-field: YouTube/LinkedIn/Facebook/Instagram/X) -------


class SocialConnectorUpdate(BaseModel):
    """Body for setting a connector's fields. A field mapped to "" (or omitted-then-null) is
    cleared; any other value is stored. Unknown field keys are ignored."""

    values: dict[str, str | None] = Field(default_factory=dict)


def _connector_or_404(connector_id: str) -> None:
    if not is_known_connector(connector_id):
        raise HTTPException(status_code=404, detail=f"Unknown connector {connector_id!r}")


def _single_connector(connector_id: str, owner: str) -> dict[str, object]:
    for row in social_connector_status(owner):
        if row["id"] == connector_id:
            return row
    raise HTTPException(status_code=404, detail=f"Unknown connector {connector_id!r}")


@router.get("/social-connectors")
def list_social_connectors(current: str = Depends(current_user)) -> list[dict[str, object]]:
    """This user's per-platform publishing-credential status. No raw secrets are returned."""
    return social_connector_status(current)


@router.put("/social-connectors/{connector_id}")
def set_social_connector(
    connector_id: str,
    body: SocialConnectorUpdate,
    current: str = Depends(current_user),
) -> dict[str, object]:
    """Set/clear a connector's credential fields (only keys belonging to this connector)."""
    _connector_or_404(connector_id)
    store = get_secrets_store()
    allowed = set(connector_field_keys(connector_id))
    for key, value in body.values.items():
        if key not in allowed:
            continue  # ignore stray keys — never let one connector write another's fields
        if value is None or not value.strip():
            store.clear(current, key)
        else:
            try:
                store.set(current, key, value)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=f"{key}: {exc}") from exc
    return _single_connector(connector_id, current)


@router.delete("/social-connectors/{connector_id}")
def clear_social_connector(
    connector_id: str,
    current: str = Depends(current_user),
) -> dict[str, object]:
    """Remove THIS USER's stored credentials for a connector (fields fall back to env)."""
    _connector_or_404(connector_id)
    store = get_secrets_store()
    for key in connector_field_keys(connector_id):
        store.clear(current, key)
    return _single_connector(connector_id, current)


@router.get("/media-token")
def media_token(current: str = Depends(current_user)) -> dict[str, object]:
    """A short-lived, MEDIA-SCOPED token for browser-native resource loads.

    `<video src>`, `<img src>` and download links are fetched by the browser, which can't attach
    the Authorization header — so the frontend appends this as `?t=`. It only unlocks media and
    downloads (scope-checked), never the rest of the API, and it expires within the hour.
    """
    return {
        "token": create_token(current, ttl_seconds=MEDIA_TOKEN_TTL_SECONDS, scope="media"),
        "expiresIn": MEDIA_TOKEN_TTL_SECONDS,
    }


@router.get("/info")
def system_info() -> dict[str, object]:
    """Runtime info + feature flags for the Settings / Integrations views."""
    s = get_settings()
    return {
        "appName": s.app_name,
        "version": __version__,
        "env": s.app_env,
        "agents": len(AGENT_REGISTRY),
        "authEnabled": s.auth_enabled,
        # Per-user private workspaces: sign-in IS required in this mode, independently of the
        # legacy AUTH_ENABLED bearer gate. The UI reports the EFFECTIVE mode from both flags.
        "perUserWorkspaces": per_user_mode(),
        # Lets the UI swap Run -> Preview where launching processes is disabled (shared hosts).
        "appRunnerEnabled": get_settings().app_runner_enabled,
        "rateLimitEnabled": s.rate_limit_enabled,
        "securityHeaders": s.security_headers_enabled,
        "supabaseConfigured": supabase_configured(s),
        "maxRecursion": s.max_recursion,
        "providers": get_provider_registry().status(),
    }
