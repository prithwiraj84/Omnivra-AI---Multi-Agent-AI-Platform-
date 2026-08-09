"""FastAPI dependencies for the REST API.

``get_repo`` resolves the process-wide dashboard repository (Supabase when configured,
else seed). ``current_user`` is the identity that OWNS a request's data (per-user isolation);
``require_user`` is the older auth gate kept for endpoints that only need "is authenticated".
"""
from __future__ import annotations

from functools import lru_cache

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Query

from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import verify_token
from app.db.repositories import DashboardRepository, get_repository
from app.services.project_store import get_project_store
from app.services.provider_keys import set_key_owner
from app.workspace_fs.paths import DEFAULT_PROJECT, safe_project_id


def get_repo() -> DashboardRepository:
    """Return the active dashboard repository."""
    return get_repository()


def _bearer(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> "jwt.PyJWKClient":
    """Cached JWKS client (it caches the fetched keys itself, so this is one fetch per process)."""
    return jwt.PyJWKClient(jwks_url, cache_keys=True)


def _decode_supabase_jwt(token: str) -> dict:
    """Verify a Supabase access token, auto-detecting how the project signs it.

    Modern projects sign with ASYMMETRIC keys (ES256/RS256) published at
    ``<SUPABASE_URL>/auth/v1/.well-known/jwks.json``; legacy projects sign with HS256 using the
    shared "JWT Secret". We read the token header and verify accordingly, so either style works
    without the operator having to know which one their project uses.
    """
    settings = get_settings()
    try:
        alg = str(jwt.get_unverified_header(token).get("alg", "")).upper()
    except Exception as exc:  # noqa: BLE001 - malformed token
        raise HTTPException(status_code=401, detail="Invalid or expired session") from exc

    opts = {"audience": settings.supabase_jwt_audience}
    if alg.startswith(("ES", "RS", "PS")):
        base = (settings.supabase_url or "").rstrip("/")
        if not base:
            # Asymmetric token but nothing to verify it against — a config error, not a bad token.
            logger.error("Per-user auth: token uses {} but SUPABASE_URL is unset (needed for JWKS).", alg)
            raise HTTPException(
                status_code=500,
                detail="Server auth misconfigured: SUPABASE_URL is required to verify this project's tokens.",
            )
        try:
            key = _jwks_client(f"{base}/auth/v1/.well-known/jwks.json").get_signing_key_from_jwt(token).key
            return jwt.decode(token, key, algorithms=["ES256", "RS256", "PS256"], **opts)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=401, detail="Invalid or expired session") from exc

    secret = settings.supabase_jwt_secret
    if not secret:
        logger.error("Per-user auth: token uses HS256 but SUPABASE_JWT_SECRET is unset.")
        raise HTTPException(
            status_code=500,
            detail="Server auth misconfigured: SUPABASE_JWT_SECRET is required to verify this project's tokens.",
        )
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], **opts)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid or expired session") from exc


def owner_from_authorization(authorization: str | None) -> str | None:
    """Best-effort: the Supabase user id in this Authorization header, or None.

    Never raises and never 401s — it exists so MIDDLEWARE can publish the key owner for the
    whole request. Enforcement stays in `current_user`.
    """
    if not per_user_mode():
        return None
    token = _bearer(authorization)
    if not token:
        return None
    try:
        sub = _decode_supabase_jwt(token).get("sub")
    except Exception:  # noqa: BLE001 - invalid token -> no owner; the dependency will 401
        return None
    return str(sub) if sub else None


def per_user_mode() -> bool:
    """True when requests are scoped to the signed-in Supabase user."""
    s = get_settings()
    return bool(s.per_user_workspaces or s.supabase_jwt_secret)


def current_user(authorization: str | None = Header(default=None)) -> str:
    """The identity that owns this request's projects/workspace.

    - PER-USER mode: verify the request's Supabase access token (ES256/RS256 via the project's
      JWKS, or HS256 via the legacy secret) and return its user id (`sub`). No/invalid -> 401.
    - Single-admin/open mode: always the admin username, so every existing test + local run
      behaves exactly as before (one owner, no auth required).
    """
    settings = get_settings()
    if not per_user_mode():
        return settings.admin_username
    token = _bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = _decode_supabase_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid session (no subject)")
    owner = str(sub)
    # Provider clients are built deep in the stack with no request in scope, so publish the
    # owner for this request's context — every resolve_provider_key() then uses THIS user's keys.
    set_key_owner(owner)
    return owner


MEDIA_TOKEN_TTL_SECONDS = 3600


def media_user(
    authorization: str | None = Header(default=None),
    t: str | None = Query(default=None),
) -> str:
    """Identity for BROWSER-NATIVE resource loads (`<video src>`, `<img src>`, download links).

    Those requests are issued by the browser itself and CANNOT carry the axios Authorization
    header, so gating them on `current_user` alone made every video/download 401 (an unplayable,
    undownloadable file). This accepts either:
      * the normal Authorization header (fetch/XHR callers), or
      * `?t=` — a short-lived, MEDIA-SCOPED token from GET /api/system/media-token.
    The media scope can't be replayed as an API session (see core.security.verify_token).
    """
    if not per_user_mode():
        return get_settings().admin_username
    if _bearer(authorization):
        return current_user(authorization)
    owner = verify_token(t, scope="media") if t else None
    if not owner:
        raise HTTPException(status_code=401, detail="Not authenticated")
    set_key_owner(owner)
    return owner


# Cookie carrying the media token for STATIC APP PREVIEWS. The preview page's relative asset
# requests (styles.css, app.js) are resolved by the browser against the page URL and DROP the
# ?t= query, so the first (tokened) request plants the token in a path-scoped cookie and the
# asset requests authenticate with that. Path-scoped so it rides ONLY preview requests.
PREVIEW_COOKIE = "omnivra_media"
PREVIEW_COOKIE_PATH = "/api/workspace/app/preview"


def preview_user(
    authorization: str | None = Header(default=None),
    t: str | None = Query(default=None),
    omnivra_media: str | None = Cookie(default=None),
) -> str:
    """`media_user` + a cookie fallback, for static app-preview requests.

    The cookie leg exists because an HTML page's relative asset URLs can't carry the ?t= token
    (see PREVIEW_COOKIE above). Same media scope, same TTL — nothing new to replay.
    """
    if not per_user_mode():
        return get_settings().admin_username
    if _bearer(authorization):
        return current_user(authorization)
    owner = verify_token(t, scope="media") if t else None
    if not owner and omnivra_media:
        owner = verify_token(omnivra_media, scope="media")
    if not owner:
        raise HTTPException(status_code=401, detail="Not authenticated")
    set_key_owner(owner)
    return owner


def _resolve_project(current: str, raw: str | None) -> str:
    """Shared project resolution: default bucket, path-jail, ownership (see get_project_id)."""
    store = get_project_store()
    if not raw or raw == DEFAULT_PROJECT:
        return store.ensure_user_default(current)
    try:
        pid = safe_project_id(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if store.get_project(pid, owner_id=current) is None:
        raise HTTPException(status_code=404, detail=f"No project {pid!r}")
    return pid


def get_media_project_id(
    current: str = Depends(media_user),
    x_project_id: str | None = Header(default=None),
    projectId: str | None = Query(default=None),
) -> str:
    """Like `get_project_id`, but usable from a plain browser URL (media + downloads)."""
    return _resolve_project(current, x_project_id or projectId)


def get_project_id(
    current: str = Depends(current_user),
    x_project_id: str | None = Header(default=None),
    projectId: str | None = Query(default=None),
) -> str:
    """Resolve the active project for a request, SCOPED TO THE CURRENT USER.

    An empty id — or the legacy shared "default" — maps to *this user's* Default Workspace
    (created on first use). Any other id must be owned by the current user, else 404 (we return
    404 rather than 403 so a crafted/foreign id never reveals another user's project existence).
    Ids that could escape the projects/ path jail are rejected with 400.
    """
    return _resolve_project(current, x_project_id or projectId)


def require_user(authorization: str | None = Header(default=None)) -> str:
    """Auth gate. Open (returns admin) unless settings.auth_enabled; else require a valid Bearer token."""
    settings = get_settings()
    if not settings.auth_enabled:
        return settings.admin_username
    token = _bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
