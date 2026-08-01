"""SecretsStore — PER-USER provider credentials, stored durably.

Every key is scoped to an OWNER (the Supabase user id in per-user mode, else the admin username),
so each signed-in user configures their own providers and never sees anyone else's.

Two backends, chosen automatically:

  * **Supabase** (when SUPABASE_URL + service-role key are set) — the durable one. Required for any
    hosted deployment: container filesystems on Hugging Face Spaces / Render / Fly are EPHEMERAL,
    so a file-backed key would silently vanish on the next restart (exactly the "I saved my keys
    and they say Not configured again" failure).
  * **Local JSON** (`workspace/.state/provider_keys.json`) — the offline/dev fallback. Atomic
    (temp file + ``os.replace``) and guarded by a process-wide RLock. Gitignored.

A monotonic EPOCH is bumped on every write; the provider registry compares it to refresh cached
provider clients in place, so a newly-saved key takes effect on the very next call.
"""
from __future__ import annotations

import json
import os
import threading
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import logger

_SCHEMA_VERSION = 2  # v1 was a flat {provider: key}; v2 nests under an owner id
_TABLE = "provider_keys"


def _validate(value: str) -> str:
    """Normalize + reject values that can't be a single usable credential."""
    key = (value or "").strip()
    if not key:
        raise ValueError("API key must not be empty.")
    if len(key) > 4096:
        raise ValueError("API key is unreasonably long.")
    # parse_api_keys treats commas/whitespace as a POOL separator, so a stray one would silently
    # split a single key into bogus fragments. Multi-key pools stay an env-only power feature.
    if any(ch.isspace() for ch in key) or "," in key:
        raise ValueError("Enter a single API key (no spaces or commas).")
    return key


class SecretsStore:
    """Owner-scoped credential store. Supabase-backed when configured, else atomic local JSON."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.RLock()
        self._epoch = 0

    # -- backend selection --------------------------------------------------
    @property
    def _db(self):  # noqa: ANN202 - the supabase client is optional/lazy
        """The Supabase client, or None when unconfigured (falls back to local JSON)."""
        try:
            from app.db.client import get_supabase_client

            return get_supabase_client()
        except Exception:  # noqa: BLE001 - never let storage wiring crash a request
            return None

    @property
    def durable(self) -> bool:
        """True when keys survive a restart (i.e. they're in Supabase, not a container disk)."""
        return self._db is not None

    # -- local JSON fallback ------------------------------------------------
    def _load_file(self) -> dict[str, dict[str, str]]:
        """{owner: {provider: key}}, tolerating a missing/corrupt/v1 file."""
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("SecretsStore: could not read {} ({}); treating as empty", self._path, exc)
            return {}
        if not isinstance(raw, dict):
            return {}
        owners = raw.get("owners")
        if isinstance(owners, dict):  # v2
            return {
                str(o): {str(p): str(v) for p, v in keys.items() if isinstance(v, str) and v.strip()}
                for o, keys in owners.items()
                if isinstance(keys, dict)
            }
        legacy = raw.get("keys")  # v1 -> everything belonged to the single admin
        if isinstance(legacy, dict):
            admin = get_settings().admin_username
            return {admin: {str(p): str(v) for p, v in legacy.items() if isinstance(v, str) and v.strip()}}
        return {}

    def _save_file(self, data: dict[str, dict[str, str]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"version": _SCHEMA_VERSION, "owners": data}, indent=2)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, self._path)  # atomic on POSIX and Windows

    # -- reads --------------------------------------------------------------
    def get(self, owner: str, provider: str) -> str | None:
        """The stored key for (owner, provider), or None."""
        db = self._db
        if db is not None:
            try:
                res = (
                    db.table(_TABLE)
                    .select("value")
                    .eq("owner_id", owner)
                    .eq("provider", provider)
                    .limit(1)
                    .execute()
                )
                rows = res.data or []
                return str(rows[0]["value"]) if rows else None
            except Exception as exc:  # noqa: BLE001 - degrade to "unset" rather than 500
                logger.warning("SecretsStore: Supabase read failed ({}); treating as unset", exc)
                return None
        with self._lock:
            return self._load_file().get(owner, {}).get(provider)

    def stored_providers(self, owner: str) -> set[str]:
        """Providers this owner has a stored key for."""
        db = self._db
        if db is not None:
            try:
                res = db.table(_TABLE).select("provider").eq("owner_id", owner).execute()
                return {str(r["provider"]) for r in (res.data or [])}
            except Exception as exc:  # noqa: BLE001
                logger.warning("SecretsStore: Supabase list failed ({}); treating as empty", exc)
                return set()
        with self._lock:
            return set(self._load_file().get(owner, {}))

    @property
    def epoch(self) -> int:
        """Monotonic counter bumped on every write (drives provider-client refresh)."""
        return self._epoch

    # -- writes -------------------------------------------------------------
    def set(self, owner: str, provider: str, value: str) -> None:
        """Store (or replace) a key for this owner. Raises ValueError on an invalid value."""
        key = _validate(value)
        db = self._db
        if db is not None:
            db.table(_TABLE).upsert(
                {"owner_id": owner, "provider": provider, "value": key},
                on_conflict="owner_id,provider",
            ).execute()
            self._epoch += 1
            return
        with self._lock:
            data = self._load_file()
            data.setdefault(owner, {})[provider] = key
            self._save_file(data)
            self._epoch += 1

    def clear(self, owner: str, provider: str) -> bool:
        """Remove a stored key. Returns True if one was present."""
        db = self._db
        if db is not None:
            try:
                res = db.table(_TABLE).delete().eq("owner_id", owner).eq("provider", provider).execute()
                existed = bool(res.data)
            except Exception as exc:  # noqa: BLE001
                logger.warning("SecretsStore: Supabase delete failed ({})", exc)
                return False
            if existed:
                self._epoch += 1
            return existed
        with self._lock:
            data = self._load_file()
            existed = provider in data.get(owner, {})
            if existed:
                data[owner].pop(provider, None)
                self._save_file(data)
                self._epoch += 1
            return existed


@lru_cache(maxsize=1)
def get_secrets_store() -> SecretsStore:
    """Process-wide SecretsStore (Supabase-backed when configured, else workspace JSON)."""
    path = Path(get_settings().workspace_path) / ".state" / "provider_keys.json"
    return SecretsStore(path)
