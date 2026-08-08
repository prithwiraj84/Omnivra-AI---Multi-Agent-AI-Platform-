"""Content-language tests (cp-0068): the script and the voice must agree on the language.

The property that actually matters is the routing one: Groq's speech models are ENGLISH-ONLY
and will "read" Devanagari as mangled phonetics instead of erroring, so a Hindi reel reaching
Groq produces confidently wrong audio. These tests pin that door shut, then check the rest of
the plumbing (prompt directive, offline fallback copy, duration parsing, persistence).
"""
from __future__ import annotations

import asyncio
import re

import pytest
from fastapi.testclient import TestClient

from app.services import elevenlabs_tts, hf_tts, media as media_mod
from app.services.languages import ENGLISH, HINDI, get_language, language_options, normalize_digits
from app.services.social import SocialService, requested_duration_sec, resolve_language

DEVANAGARI = re.compile(r"[ऀ-ॿ]")


# --- routing: the one that can silently produce garbage ---------------------------------


def test_hindi_never_routes_to_groq() -> None:
    """Groq's playai-tts/Orpheus are English models. Hindi must not list them at all."""
    assert "groq" not in HINDI.tts_chain
    assert HINDI.tts_chain[0] == "elevenlabs", "the natural-sounding engine goes first"
    assert "groq" in ENGLISH.tts_chain, "English keeps its free fallback"


def test_hindi_with_only_groq_configured_stays_silent_with_an_honest_note(monkeypatch) -> None:
    """A Groq-only account gets NO Hindi audio — and is told exactly which key would fix it,
    rather than a reel narrated in phonetic gibberish."""
    calls: list[str] = []

    class _Groq:
        is_configured = True

        async def generate_audio(self, **_kw):  # noqa: ANN003
            calls.append("groq")
            return b"RIFFshould-never-happen"

    monkeypatch.setattr(elevenlabs_tts, "is_configured", lambda: False)
    monkeypatch.setattr(hf_tts, "is_configured", lambda _lang="hi": False)
    monkeypatch.setattr(media_mod, "get_provider_registry", lambda: type("R", (), {"get": staticmethod(lambda _n: _Groq())})())

    rel, note = asyncio.run(media_mod.MediaService()._tts("नमस्ते दुनिया", "default", "hi"))

    assert rel is None
    assert calls == [], "Groq must never be asked to speak Hindi"
    assert "English-only" in note, note
    assert "ElevenLabs" in note and "Hugging Face" in note, note


def test_hindi_prefers_elevenlabs_and_passes_the_language_through(monkeypatch) -> None:
    seen: list[str] = []

    async def fake_synth(text, *, language="en"):  # noqa: ANN001
        seen.append(language)
        return b"ID3fake-mp3"

    monkeypatch.setattr(elevenlabs_tts, "is_configured", lambda: True)
    monkeypatch.setattr(elevenlabs_tts, "synthesize", fake_synth)

    rel, note = asyncio.run(media_mod.MediaService()._tts("नमस्ते", "default", "hi"))
    assert rel and rel.endswith(".mp3")
    assert seen == ["hi"], "the engine must be told which language to speak"
    assert "Hindi" in note


def test_hindi_falls_back_to_hugging_face_when_elevenlabs_is_absent(monkeypatch) -> None:
    """No ElevenLabs key still gets REAL Hindi audio via the free MMS model."""
    seen: list[str] = []

    async def fake_hf(text, *, language="hi"):  # noqa: ANN001
        seen.append(language)
        return b"RIFFfake-wav"

    monkeypatch.setattr(elevenlabs_tts, "is_configured", lambda: False)
    monkeypatch.setattr(hf_tts, "is_configured", lambda _lang="hi": True)
    monkeypatch.setattr(hf_tts, "synthesize", fake_hf)

    rel, note = asyncio.run(media_mod.MediaService()._tts("नमस्ते", "default", "hi"))
    assert rel and rel.endswith(".wav")
    assert seen == ["hi"]
    # The quality trade must be stated, not hidden.
    assert "ElevenLabs" in note and "free" in note.lower()


def test_english_chain_is_unchanged(monkeypatch) -> None:
    """Regression guard: adding languages must not alter the English path at all."""
    used: list[str] = []

    class _Groq:
        is_configured = True

        async def generate_audio(self, *, text, model, voice, response_format):  # noqa: ANN001
            used.append("groq")
            return b"RIFFgroq-wav"

    monkeypatch.setattr(elevenlabs_tts, "is_configured", lambda: False)
    monkeypatch.setattr(media_mod, "get_provider_registry", lambda: type("R", (), {"get": staticmethod(lambda _n: _Groq())})())

    rel, _note = asyncio.run(media_mod.MediaService()._tts("hello", "default"))
    assert rel and used == ["groq"]


# --- ElevenLabs model selection ---------------------------------------------------------


def test_english_only_elevenlabs_model_is_upgraded_for_hindi(monkeypatch) -> None:
    """An English-only model would mangle Devanagari rather than fail, so it gets swapped."""
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "elevenlabs_model", "eleven_monolingual_v1", raising=False)
    assert elevenlabs_tts._model_for("hi") == "eleven_multilingual_v2"
    assert elevenlabs_tts._model_for("en") == "eleven_monolingual_v1", "English keeps the user's choice"


def test_per_language_voice_override(monkeypatch) -> None:
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "elevenlabs_voice_id", "english-voice", raising=False)
    monkeypatch.setattr(s, "elevenlabs_voice_id_hi", "hindi-voice", raising=False)
    assert elevenlabs_tts._configured_voice_for("hi") == "hindi-voice"
    assert elevenlabs_tts._configured_voice_for("en") == "english-voice"

    # With no Hindi-specific voice it falls back to the general one rather than failing.
    monkeypatch.setattr(s, "elevenlabs_voice_id_hi", None, raising=False)
    assert elevenlabs_tts._configured_voice_for("hi") == "english-voice"


# --- language resolution + duration parsing ---------------------------------------------


@pytest.mark.parametrize(
    ("brief", "expected"),
    [
        ("दो मिनट का वीडियो", 120.0),
        ("४५ सेकंड की रील", 45.0),  # Devanagari digits
        ("एक मिनट", 60.0),
        ("45 सेकंड", 45.0),
        ("1 minute video on python", 60.0),  # English still works
        ("90-second clip", 90.0),
        ("no duration here", None),
    ],
)
def test_duration_is_parsed_in_both_scripts(brief: str, expected: float | None) -> None:
    assert requested_duration_sec(brief) == expected


@pytest.mark.parametrize(
    "brief",
    [
        "Reel for Instagram about our launch",  # "Instagr-am"
        "a reel about our team culture",  # "te-am"
        "Promote our new program",  # "progr-am"
        "what this means for you",  # "me-ans"
        "How the platform was built",  # "w-as"
        "buy our phones",  # "ph-ones"
        "a reel about dogs",
    ],
)
def test_ordinary_words_are_not_read_as_a_duration(brief: str) -> None:
    """The bare 'a'/'m'/'s' alternatives must not match INSIDE a word.

    Without a left word boundary "Instagram" parsed as a + m = one minute, so an ordinary
    brief silently produced a 60s reel instead of the 30s default.
    """
    assert requested_duration_sec(brief) is None


def test_a_latin_word_cannot_outrank_the_real_duration() -> None:
    """search() returns the FIRST match, so a false positive early in the string used to
    override the duration the user actually asked for later in it."""
    assert requested_duration_sec("Instagram के लिए 30 सेकंड की रील") == 30.0
    assert requested_duration_sec("हमारे team पर 45 सेकंड की रील") == 45.0
    assert requested_duration_sec("Instagram reel, 30 seconds") == 30.0


def test_hindi_inflected_units_still_parse() -> None:
    """The right-hand guard must not reject Hindi's oblique/plural forms."""
    assert requested_duration_sec("45 सेकंडों में") == 45.0


def test_explicit_language_beats_the_briefs_script() -> None:
    assert resolve_language("en", "नमस्ते दुनिया") == "en", "the user's pick is authoritative"
    assert resolve_language("hi", "hello world") == "hi"
    assert resolve_language(None, "नमस्ते दुनिया") == "hi", "a Devanagari brief infers Hindi"
    assert resolve_language(None, "hello world") == "en"
    assert resolve_language("klingon", "hello") == "en", "an unknown code degrades, never raises"


def test_normalize_digits() -> None:
    assert normalize_digits("४५ सेकंड") == "45 सेकंड"
    assert normalize_digits("45s") == "45s"


# --- offline fallback copy ---------------------------------------------------------------


def test_hindi_fallback_storyboard_is_actually_hindi() -> None:
    sb = SocialService._fallback_storyboard("पायथन कैसे सीखें", 30.0, "hi")
    assert sb.language == "hi"
    assert DEVANAGARI.search(sb.scenes[0].voiceover), "narration must be in Devanagari"
    assert DEVANAGARI.search(sb.call_to_action)


def test_broll_queries_stay_english_even_for_a_hindi_reel() -> None:
    """Pexels only indexes English — a Devanagari search term returns nothing, so the reel
    would silently lose all of its stock footage."""
    sb = SocialService._fallback_storyboard("पायथन प्रोग्रामिंग सीखिए", 40.0, "hi")
    for scene in sb.scenes:
        assert scene.broll_query, "every scene needs a searchable b-roll term"
        assert not DEVANAGARI.search(scene.broll_query), f"b-roll query must be English: {scene.broll_query!r}"


def test_english_fallback_storyboard_is_unchanged() -> None:
    sb = SocialService._fallback_storyboard("Launch our AI company OS", 30.0)
    assert sb.language == "en"
    assert "changes everything" in sb.scenes[0].voiceover


def test_hindi_scripts_are_sized_for_a_slower_spoken_pace() -> None:
    """Hindi words carry more syllables, so the same second holds fewer of them. Sizing a
    Hindi script with English pacing is what makes narration overrun its scene."""
    assert HINDI.words_per_second < ENGLISH.words_per_second


# --- API surface -------------------------------------------------------------------------


def test_languages_endpoint(client: TestClient) -> None:
    res = client.get("/api/social/languages")
    assert res.status_code == 200
    codes = {row["code"] for row in res.json()}
    assert codes == {"en", "hi"}
    assert res.json() == language_options()


def test_draft_reel_in_hindi_persists_the_language(client: TestClient) -> None:
    body = client.post("/api/social/reel", json={"brief": "पायथन कैसे सीखें", "language": "hi"}).json()
    assert body["language"] == "hi"
    # Stored ON the storyboard too, so a re-render months later still picks a Hindi voice.
    assert body["storyboard"]["language"] == "hi"
    assert DEVANAGARI.search(body["storyboard"]["scenes"][0]["voiceover"])

    # And it survives the round-trip through the store.
    again = client.get(f"/api/social/drafts/{body['id']}").json()
    assert again["language"] == "hi" and again["storyboard"]["language"] == "hi"


def test_draft_reel_defaults_to_english(client: TestClient) -> None:
    body = client.post("/api/social/reel", json={"brief": "Launch our AI company OS"}).json()
    assert body["language"] == "en"
    assert body["storyboard"]["language"] == "en"


def test_draft_reel_infers_hindi_from_a_devanagari_brief(client: TestClient) -> None:
    """A user who types entirely in Hindi shouldn't have to find the toggle first."""
    body = client.post("/api/social/reel", json={"brief": "एआई से कंटेंट कैसे बनाएँ"}).json()
    assert body["language"] == "hi"


def test_draft_post_in_hindi(client: TestClient) -> None:
    body = client.post("/api/social/post", json={"brief": "हमारी नई एआई कंपनी", "language": "hi"}).json()
    assert body["language"] == "hi"
    assert DEVANAGARI.search(body["caption"])
    # Hashtags stay Latin so they remain searchable cross-platform.
    assert all(not DEVANAGARI.search(tag) for tag in body["hashtags"])


def test_unknown_language_is_rejected_by_the_schema(client: TestClient) -> None:
    res = client.post("/api/social/reel", json={"brief": "x", "language": "klingon"})
    assert res.status_code == 422


def test_old_drafts_without_a_language_still_load() -> None:
    """Drafts persisted before languages existed must not fail validation."""
    from app.schemas.social import ReelStoryboard, SocialDraft

    draft = SocialDraft(id="reel_x", project_id="p", kind="reel", brief="b", created_at="now")
    assert draft.language == "en"
    assert ReelStoryboard(title="t").language == "en"
    assert get_language(None) is ENGLISH
