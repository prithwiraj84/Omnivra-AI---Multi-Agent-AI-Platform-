"""X (Twitter) publisher — real text tweet via API v2 + OAuth 1.0a, guarded + stub-safe.

Posting requires OAuth 1.0a user-context keys (consumer key/secret + access token/secret);
the read-only bearer token can't post. The signing is implemented with the stdlib (hmac +
hashlib), so no extra dependency. Without the four keys it stubs. Never raises: failures
return ok=False with a generic note (keys are never echoed).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
import urllib.parse

import httpx

from app.core.logging import logger
from app.schemas.social import PublishResult, SocialDraft
from app.services.post_text import build_post_text
from app.services.provider_keys import connector_configured, resolve_provider_key

_TWEETS_URL = "https://api.twitter.com/2/tweets"
_MAX_CHARS = 280


def _pct(value: object) -> str:
    """RFC 3986 percent-encoding (OAuth reserves only unreserved chars; ~ stays literal)."""
    return urllib.parse.quote(str(value), safe="~")


def signature_base_string(method: str, url: str, params: dict[str, str]) -> str:
    """The OAuth 1.0a signature base string: METHOD & enc(url) & enc(sorted&encoded params).

    Per RFC 5849 §3.4.1.3.2, params are percent-encoded FIRST, then sorted by the encoded
    name (then encoded value) — matters only if `extra_params` with reserved chars are ever
    signed (today's oauth_* keys are all unreserved, so encoded order == raw order)."""
    encoded = sorted((_pct(k), _pct(v)) for k, v in params.items())
    normalized = "&".join(f"{k}={v}" for k, v in encoded)
    return "&".join([method.upper(), _pct(url), _pct(normalized)])


def _sign(base: str, consumer_secret: str, token_secret: str) -> str:
    key = f"{_pct(consumer_secret)}&{_pct(token_secret)}".encode()
    digest = hmac.new(key, base.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def oauth1_header(
    method: str,
    url: str,
    *,
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_secret: str,
    extra_params: dict[str, str] | None = None,
    nonce: str | None = None,
    timestamp: str | None = None,
) -> str:
    """Build the `Authorization: OAuth …` header for a signed request.

    `extra_params` are any query/body form params that participate in the signature (none for a
    JSON-body v2 tweet). Only the oauth_* params go into the header itself.
    """
    oauth = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp or str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    all_params = {**oauth, **(extra_params or {})}
    base = signature_base_string(method, url, all_params)
    oauth["oauth_signature"] = _sign(base, consumer_secret, access_secret)
    return "OAuth " + ", ".join(f'{_pct(k)}="{_pct(v)}"' for k, v in sorted(oauth.items()))


def is_configured() -> bool:
    return connector_configured("twitter")


def _stub(draft: SocialDraft) -> PublishResult:
    return PublishResult(
        platform="twitter",
        ok=True,
        stub=True,
        url=f"https://twitter.local/stub/{draft.id}",
        note="Add X (Twitter) OAuth 1.0a keys in Integrations to post for real; recorded as a stub.",
    )


async def publish(draft: SocialDraft) -> PublishResult:
    """Publish the draft as a tweet. Stub-safe + never raises."""
    if not is_configured():
        return _stub(draft)
    text = build_post_text(draft, _MAX_CHARS)
    if not text:
        return PublishResult(platform="twitter", ok=False, stub=False, note="Nothing to post — the draft has no caption or brief.")
    ck = resolve_provider_key("twitter_api_key")
    cs = resolve_provider_key("twitter_api_secret")
    at = resolve_provider_key("twitter_access_token")
    ats = resolve_provider_key("twitter_access_secret")
    try:
        header = oauth1_header(
            "POST", _TWEETS_URL,
            consumer_key=ck or "", consumer_secret=cs or "",
            access_token=at or "", access_secret=ats or "",
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _TWEETS_URL,
                headers={"Authorization": header, "Content-Type": "application/json"},
                json={"text": text},
            )
            resp.raise_for_status()
        tweet_id = (resp.json().get("data") or {}).get("id")
        url = f"https://twitter.com/i/web/status/{tweet_id}" if tweet_id else None
        return PublishResult(platform="twitter", ok=True, stub=False, url=url, note="Posted to X (Twitter).")
    except Exception as exc:  # noqa: BLE001
        logger.error("X (Twitter) post failed ({}): {}", type(exc).__name__, str(exc)[:200])
        return PublishResult(platform="twitter", ok=False, stub=False, note=f"X (Twitter) post failed ({type(exc).__name__}); see server logs.")
