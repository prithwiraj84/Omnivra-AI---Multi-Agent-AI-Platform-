"""Content languages — the one table that decides how a language changes generation.

The Social Studio lets the user pick the language of a reel/post, and that single choice has
to reach three very different places at once:

  1. the LLM prompt      — so the SCRIPT is actually written in that language
  2. the speech engine   — so the VOICE speaks it (and we don't hand Devanagari to an
                           English-only model, which produces garbage rather than an error)
  3. the offline fallback — so an install with no provider keys still drafts readable copy

Keeping all three in one place is what stops them drifting apart. Adding a language means
adding one `Language` entry here; nothing else in the pipeline needs to know the list.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

LanguageCode = Literal["en", "hi"]
DEFAULT_LANGUAGE: LanguageCode = "en"


@dataclass(frozen=True, slots=True)
class Language:
    """Everything the pipeline needs to know about one content language."""

    code: str
    name: str  # English name, used in prompts and notes
    native_name: str  # how a speaker writes it, used in the UI

    # --- script generation ---
    script_directive: str  # appended to the LLM prompt; the strongest lever on output language
    words_per_second: float  # narration pace, used to size each scene's script

    # --- speech ---
    # Engines to try IN ORDER. 'groq' is English-only (playai-tts / Orpheus are English models),
    # so it must never appear for another language: it would happily "speak" transliterated
    # nonsense instead of failing, which is worse than no audio. 'google' (Gemini TTS) is the
    # free multilingual engine and runs on the Google AI key the LLM agents already use.
    tts_chain: tuple[str, ...]
    elevenlabs_needs_multilingual: bool  # force a multilingual model regardless of settings

    # --- offline fallback copy (no LLM key configured) ---
    fallback_beats: tuple[tuple[str, str], ...]  # (on-screen caption, spoken line)
    fallback_cta: str
    fallback_post_tail: str

    # How much bigger the LLM token budget has to be than for English. Non-Latin scripts
    # tokenize far worse under BPE, so an unscaled budget truncates the JSON mid-storyboard.
    token_factor: float = 1.0

    # Generic b-roll search terms (ALWAYS English — Pexels only indexes English) used when the
    # brief itself yields no usable Latin keywords, which is the norm for a Devanagari brief.
    fallback_broll: tuple[str, ...] = ("technology", "team working", "city timelapse", "data screen", "future tech")


ENGLISH = Language(
    code="en",
    name="English",
    native_name="English",
    script_directive=(
        "Write every 'voiceover' and 'onScreenText' in natural, conversational ENGLISH."
    ),
    words_per_second=2.4,
    tts_chain=("elevenlabs", "google", "groq"),
    elevenlabs_needs_multilingual=False,
    fallback_beats=(
        ("Hook: stop the scroll", "Here's how {topic} changes everything."),
        ("The problem", "Most teams still do this the slow, manual way."),
        ("The shift", "Omnivra's AI company handles it end to end."),
        ("Proof", "Faster output, fewer errors — with human approval on every step."),
        ("Call to action", "Follow to see your AI workforce in action."),
    ),
    fallback_cta="Follow for more.",
    fallback_post_tail="Built by Omnivra — your autonomous AI company. Human-approved, every time.",
)

HINDI = Language(
    code="hi",
    name="Hindi",
    native_name="हिन्दी",
    script_directive=(
        "Write every 'voiceover' and 'onScreenText' in natural, conversational HINDI using the "
        "Devanagari script (हिन्दी). Do NOT use Roman/Latin transliteration and do NOT write them "
        "in English. Everyday spoken Hindi is right — the kind a person actually says out loud, "
        "not formal literary Hindi. Common English loanwords that Hindi speakers really use "
        "(AI, video, team) may stay as-is. IMPORTANT: 'brollQuery' is a stock-footage search term "
        "and must stay in ENGLISH."
    ),
    # Hindi words carry more syllables each, so the same clock second holds fewer of them.
    # Overestimating here is what makes narration run past the end of its scene.
    words_per_second=2.0,
    # NO Groq: playai-tts and Orpheus are English-only models. ElevenLabs multilingual is the
    # premium path; Gemini TTS is the free one and speaks Hindi natively. (Hugging Face is NOT
    # here: its serverless tier no longer hosts ANY text-to-speech model.)
    tts_chain=("elevenlabs", "google"),
    elevenlabs_needs_multilingual=True,
    fallback_beats=(
        ("रुकिए, ये देखिए", "{topic} — ये आपके काम करने का तरीका पूरी तरह बदल देगा।"),
        ("समस्या क्या है", "आज भी ज़्यादातर टीमें यह सारा काम हाथ से, धीरे-धीरे करती हैं।"),
        ("नया तरीका", "ओमनिव्रा की एआई कंपनी यह पूरा काम शुरू से आखिर तक खुद संभाल लेती है।"),
        ("नतीजा", "काम तेज़, गलतियाँ कम — और हर कदम पर आपकी मंज़ूरी ज़रूरी।"),
        ("अब आपकी बारी", "फॉलो कीजिए और अपनी एआई टीम को काम करते हुए देखिए।"),
    ),
    fallback_cta="और जानने के लिए फॉलो कीजिए।",
    fallback_post_tail="ओमनिव्रा द्वारा निर्मित — आपकी अपनी स्वायत्त एआई कंपनी। हर पोस्ट, आपकी मंज़ूरी के बाद।",
    token_factor=1.6,
)

LANGUAGES: dict[str, Language] = {lang.code: lang for lang in (ENGLISH, HINDI)}


def get_language(code: str | None) -> Language:
    """The Language for ``code``, defaulting to English for anything unknown/missing.

    Never raises: an old draft persisted before languages existed, or a client sending a code
    we don't support, degrades to English rather than breaking generation.
    """
    return LANGUAGES.get((code or "").strip().lower(), ENGLISH)


def language_options() -> list[dict[str, str]]:
    """The selectable languages, for the UI / API discovery."""
    return [{"code": lang.code, "name": lang.name, "nativeName": lang.native_name} for lang in LANGUAGES.values()]


# --- brief normalization -----------------------------------------------------------------
# A Hindi brief may carry Devanagari digits (२ मिनट). Fold them to ASCII before any numeric
# parsing so the duration regex sees "2 मिनट" and behaves exactly as it does for English.
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalize_digits(text: str) -> str:
    """Fold Devanagari digits to ASCII so numeric parsing is script-agnostic."""
    return (text or "").translate(_DEVANAGARI_DIGITS)


def detect_language(brief: str) -> str | None:
    """The language a brief is WRITTEN in, when it's unambiguous — else None.

    Only used as a hint when the caller didn't pick a language explicitly: a brief typed in
    Devanagari almost certainly wants a Hindi reel. An explicit choice always wins.
    """
    if re.search(r"[ऀ-ॿ]", brief or ""):
        return "hi"
    return None
