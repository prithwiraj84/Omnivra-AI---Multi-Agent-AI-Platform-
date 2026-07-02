"""Supabase Storage upload — puts a workspace file in the configured bucket and returns a
temporary, publicly-fetchable **signed URL**.

Used by the Instagram publisher: Instagram *pulls* a reel from a URL rather than accepting an
upload, so the rendered `.mp4` must be reachable over the public internet first. Signed URLs are
preferred over a public bucket — they don't require the bucket to be public and they auto-expire.

Talks to the Storage REST API directly over httpx (no `supabase` SDK dependency). Guarded:
`is_configured()` is false unless Supabase URL + service-role key are set; `upload_signed()`
returns None when unconfigured and raises only on a genuine HTTP failure (the caller wraps it).
"""
from __future__ import annotations

from pathlib import Path

import httpx

from app.core.config import get_settings
from app.db.client import supabase_configured


def is_configured() -> bool:
    return supabase_configured(get_settings())


async def upload_signed(
    local_path: Path,
    dest_path: str,
    *,
    content_type: str = "application/octet-stream",
    expires_in: int = 3600,
) -> str | None:
    """Upload `local_path` to `<bucket>/<dest_path>` and return a signed URL (valid `expires_in`
    seconds), or None when Supabase Storage isn't configured. Raises on HTTP failure."""
    s = get_settings()
    if not supabase_configured(s):
        return None
    base = str(s.supabase_url).rstrip("/")
    bucket = s.supabase_storage_bucket
    key = s.supabase_service_role_key
    data = local_path.read_bytes()

    async with httpx.AsyncClient(timeout=180.0) as client:
        # 1) Upload (upsert so a re-publish overwrites rather than 409s).
        up = await client.post(
            f"{base}/storage/v1/object/{bucket}/{dest_path}",
            headers={"Authorization": f"Bearer {key}", "Content-Type": content_type, "x-upsert": "true"},
            content=data,
        )
        up.raise_for_status()
        # 2) Sign it for temporary public read.
        sign = await client.post(
            f"{base}/storage/v1/object/sign/{bucket}/{dest_path}",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"expiresIn": expires_in},
        )
        sign.raise_for_status()
        body = sign.json()
    signed = body.get("signedURL") or body.get("signedUrl")
    if not signed:
        return None
    # signed is like "/object/sign/<bucket>/<path>?token=..."; make it absolute.
    return f"{base}/storage/v1{signed}" if signed.startswith("/") else f"{base}/storage/v1/{signed}"
