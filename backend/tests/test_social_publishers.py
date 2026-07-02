"""Real social publishers (cp-0064 Phase B): LinkedIn / Facebook / X.

Conftest neutralizes every credential, so is_configured() is False and each publisher takes
the stub path WITHOUT touching the network. We also unit-test the OAuth 1.0a signing (the only
non-trivial, error-prone logic) against a hand-verifiable base string + the header shape.
"""
from __future__ import annotations

import asyncio

import pytest

from app.schemas.social import SocialDraft
from app.services import facebook, instagram, linkedin, storage, twitter
from app.services.post_text import build_post_text
from app.services.provider_keys import SOCIAL_CONNECTORS
from app.services.secrets_store import get_secrets_store
from app.workspace_fs.paths import project_root

_SOCIAL_KEYS = [f.key for c in SOCIAL_CONNECTORS for f in c.fields]


@pytest.fixture(autouse=True)
def _clean_social_store():
    """Isolate the shared SecretsStore singleton across these tests + other modules."""
    store = get_secrets_store()
    for k in _SOCIAL_KEYS:
        store.clear(k)
    yield
    for k in _SOCIAL_KEYS:
        store.clear(k)


def _draft(**over) -> SocialDraft:
    base = dict(
        id="d1", project_id="p1", kind="post", brief="Launch day!", created_at="2026-01-01T00:00:00Z",
        caption="We shipped Omnivra.", hashtags=["ai", "#omnivra"],
    )
    base.update(over)
    return SocialDraft(**base)


# --- shared text builder ---------------------------------------------------
def test_build_post_text_caption_hashtags_and_cap():
    text = build_post_text(_draft(), 280)
    assert text.startswith("We shipped Omnivra.")
    assert "#ai" in text and "#omnivra" in text  # bare tag gets a '#', already-# kept once
    assert text.count("#omnivra") == 1
    # falls back to brief when no caption
    assert build_post_text(_draft(caption=None), 280).startswith("Launch day!")
    # hard cap
    assert len(build_post_text(_draft(caption="x" * 500, hashtags=[]), 280)) == 280


# --- unconfigured => stub, no network --------------------------------------
def test_publishers_stub_without_credentials():
    for mod, name in ((linkedin, "linkedin"), (facebook, "facebook"), (twitter, "twitter")):
        assert mod.is_configured() is False
        res = asyncio.run(mod.publish(_draft()))
        assert res.platform == name
        assert res.ok is True and res.stub is True  # stub-safe: flow still completes offline
        assert ".local/stub/" in (res.url or "")


# --- OAuth 1.0a signing ----------------------------------------------------
def test_oauth1_signature_base_string_is_rfc_correct():
    params = {
        "oauth_consumer_key": "ck",
        "oauth_nonce": "abc",
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": "1700000000",
        "oauth_token": "at",
        "oauth_version": "1.0",
    }
    base = twitter.signature_base_string("post", "https://api.twitter.com/2/tweets", params)
    assert base == (
        "POST&https%3A%2F%2Fapi.twitter.com%2F2%2Ftweets&"
        "oauth_consumer_key%3Dck%26oauth_nonce%3Dabc%26"
        "oauth_signature_method%3DHMAC-SHA1%26oauth_timestamp%3D1700000000%26"
        "oauth_token%3Dat%26oauth_version%3D1.0"
    )


def test_instagram_stub_without_credentials():
    assert instagram.is_configured() is False
    res = asyncio.run(instagram.publish(_draft(kind="reel", video_path="r.mp4")))
    assert res.platform == "instagram" and res.ok is True and res.stub is True


def test_storage_unconfigured_in_tests():
    # conftest neutralizes SUPABASE_* -> storage is off, so Instagram's real path is gated.
    assert storage.is_configured() is False


def test_instagram_configured_gates_on_video_then_storage():
    store = get_secrets_store()
    store.set("instagram_user_id", "123")
    store.set("instagram_access_token", "IGtoken")
    assert instagram.is_configured() is True

    # no rendered video yet -> render-first note (before any network/storage)
    res = asyncio.run(instagram.publish(_draft(kind="reel", video_path=None)))
    assert res.ok is False and "Render the reel" in res.note

    # video present but Supabase Storage not configured -> clear note, still no network
    pid = "p_ig_test"
    root = project_root(pid)
    root.mkdir(parents=True, exist_ok=True)
    (root / "reel.mp4").write_bytes(b"\x00\x00fake-mp4-bytes")
    res2 = asyncio.run(instagram.publish(_draft(kind="reel", project_id=pid, video_path="reel.mp4")))
    assert res2.ok is False and "Supabase Storage" in res2.note


def test_oauth1_header_deterministic_and_shaped():
    kw = dict(
        consumer_key="ck", consumer_secret="cs", access_token="at", access_secret="ats",
        nonce="fixednonce", timestamp="1700000000",
    )
    h1 = twitter.oauth1_header("POST", twitter._TWEETS_URL, **kw)
    h2 = twitter.oauth1_header("POST", twitter._TWEETS_URL, **kw)
    assert h1 == h2  # deterministic for fixed nonce/timestamp
    assert h1.startswith("OAuth ")
    for field in ("oauth_consumer_key", "oauth_nonce", "oauth_signature", "oauth_signature_method", "oauth_timestamp", "oauth_token", "oauth_version"):
        assert field in h1
    assert 'oauth_signature_method="HMAC-SHA1"' in h1
