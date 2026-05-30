"""System routes: health metrics, provider status, and runtime info."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app import __version__, schemas
from app.agents.registry import AGENT_REGISTRY
from app.api.deps import get_repo
from app.core.config import get_settings
from app.db.client import supabase_configured
from app.db.repositories import DashboardRepository
from app.providers.registry import get_provider_registry

router = APIRouter(tags=["system"])


@router.get("/health", response_model=list[schemas.HealthMetric])
def get_system_health(repo: DashboardRepository = Depends(get_repo)) -> list[schemas.HealthMetric]:
    """Return the system-health metrics."""
    return repo.get_system_health()


@router.get("/providers")
def providers() -> dict[str, bool]:
    """Provider name -> configured? (drives the Integrations view's status dots)."""
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
        "rateLimitEnabled": s.rate_limit_enabled,
        "securityHeaders": s.security_headers_enabled,
        "supabaseConfigured": supabase_configured(s),
        "maxRecursion": s.max_recursion,
        "providers": get_provider_registry().status(),
    }
