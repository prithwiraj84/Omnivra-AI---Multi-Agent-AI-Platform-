"""SecretsStore — persists user-entered provider API keys under workspace/.state.

Keys the admin types into the website (Integrations → API keys) are stored here so the
backend can USE them at call time without a restart, and so they survive reloads. This is
the single writable home for in-app secrets:

    workspace/.state/provider_keys.json   -> {"version": 1, "keys": {"<provider>": "<key>"}}

The file is gitignored (root .gitignore: ``workspace/.state/*.json``). Writes are atomic
(temp file + ``os.replace``, atomic on Windows too) and guarded by a process-wide RLock, so a
concurrent read never sees a half-written file. Plaintext-at-rest is acceptable for this
single-admin, offline-first, localhost product (same trust level as backend/.env), and the file
is never committed.

A monotonic EPOCH is bumped on every write; the provider registry compares it to refresh cached
provider clients in place (see providers/registry.py) so a newly-saved key takes effect on the
very next LLM call.
"""
from __future__ import annotations

import json
import os
import threading
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import logger

_SCHEMA_VERSION = 1


class SecretsStore:
    """Thread-safe, atomic JSON store of ``provider -> api key`` overrides."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.RLock()
        self._epoch = 0

    # -- reads -------------------------------------------------------------
    def _load(self) -> dict[str, str]:
        """Read the on-disk key map, tolerating a missing/corrupt file (returns {})."""
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (json.JSONDecodeError, OSError) as exc:  # corrupt/unreadable -> behave as empty
            logger.warning("SecretsStore: could not read {} ({}); treating as empty", self._path, exc)
            return {}
        keys = raw.get("keys") if isinstance(raw, dict) else None
        if not isinstance(keys, dict):
            return {}
        # normalize to str->str, dropping blanks
        return {str(k): str(v) for k, v in keys.items() if isinstance(v, str) and v.strip()}

    def get(self, provider: str) -> str | None:
        """The stored key for a provider, or None."""
        with self._lock:
            return self._load().get(provider)

    def stored_providers(self) -> set[str]:
        """Set of providers that currently have a stored key."""
        with self._lock:
            return set(self._load().keys())

    @property
    def epoch(self) -> int:
        """Monotonic counter bumped on every write (drives provider-client refresh)."""
        return self._epoch

    # -- writes ------------------------------------------------------------
    def set(self, provider: str, value: str) -> None:
        """Store (or replace) a provider key. Raises ValueError on an invalid value.

        Rejects commas / internal whitespace: ``parse_api_keys`` treats those as a POOL
        separator, so a stray one would silently split a single key into bogus fragments.
        Multi-key pools remain an env-only power feature.
        """
        key = (value or "").strip()
        if not key:
            raise ValueError("API key must not be empty.")
        if len(key) > 4096:
            raise ValueError("API key is unreasonably long.")
        if any(ch.isspace() for ch in key) or "," in key:
            raise ValueError("Enter a single API key (no spaces or commas).")
        with self._lock:
            data = self._load()
            data[provider] = key
            self._atomic_save(data)
            self._epoch += 1

    def clear(self, provider: str) -> bool:
        """Remove a stored key. Returns True if one was present."""
        with self._lock:
            data = self._load()
            existed = provider in data
            if existed:
                data.pop(provider, None)
                self._atomic_save(data)
                self._epoch += 1
            return existed

    def _atomic_save(self, keys: dict[str, str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"version": _SCHEMA_VERSION, "keys": keys}, indent=2)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, self._path)  # atomic on POSIX and Windows


@lru_cache(maxsize=1)
def get_secrets_store() -> SecretsStore:
    """Process-wide SecretsStore rooted at workspace/.state/provider_keys.json."""
    path = Path(get_settings().workspace_path) / ".state" / "provider_keys.json"
    return SecretsStore(path)
