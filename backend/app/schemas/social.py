"""Social content pipeline schemas (cp-0016). camelCase on the wire.

Two kinds of content, both gated by human approval before any outward publish:
  - reel: an LLM storyboard (scenes) -> (later) MoviePy+Pexels+Orpheus render -> YouTube/Instagram
  - post: an LLM caption + tags + a FLUX image -> Facebook/LinkedIn/Twitter

Phase 1 is offline/stub-first: the creative drafting + approval + publish FLOW is real,
but the heavy engines (video render) and the platform uploads are stubbed.
"""
from __future__ import annotations

from typing import Literal

from app.schemas.dashboard import CamelModel

SocialKind = Literal["reel", "post"]
# The language the SCRIPT is written in and the VOICE speaks. See services/languages.py for
# what each code actually changes (prompt directive, TTS engine chain, offline fallback copy).
ContentLanguage = Literal["en", "hi"]
ReelTarget = Literal["youtube", "instagram"]
PostTarget = Literal["facebook", "linkedin", "twitter"]

# Default publish targets per kind (the spec: reels -> YT+IG, posts -> FB+LI+X).
DEFAULT_REEL_TARGETS: list[str] = ["youtube", "instagram"]
DEFAULT_POST_TARGETS: list[str] = ["facebook", "linkedin", "twitter"]


class ReelScene(CamelModel):
    """One shot in a vertical short-form reel."""

    duration_sec: float = 4.0
    voiceover: str = ""
    broll_query: str = ""  # the Pexels search term for this scene's stock footage
    on_screen_text: str = ""


class ReelStoryboard(CamelModel):
    """The machine-readable plan the video engine renders from."""

    title: str
    hook: str = ""
    scenes: list[ReelScene] = []
    music_mood: str = "upbeat"
    call_to_action: str = ""
    total_duration_sec: float = 0.0
    # Persisted so a LATER re-render still picks the voice the script was written for.
    # Defaults to English, so storyboards drafted before languages existed still load.
    language: ContentLanguage = "en"


class PublishResult(CamelModel):
    """The outcome of (attempting to) publish a draft to one platform."""

    platform: str
    ok: bool
    url: str | None = None
    stub: bool = True
    note: str = ""


class SocialDraft(CamelModel):
    """A drafted piece of content awaiting approval, then published (stub in Phase 1)."""

    id: str
    project_id: str
    kind: SocialKind
    brief: str
    language: ContentLanguage = "en"
    status: str = "awaiting_approval"  # awaiting_approval | published | rejected
    targets: list[str] = []
    # reel payload
    storyboard: ReelStoryboard | None = None
    render_status: str = "none"  # none | rendering | rendered | failed (reels only)
    video_path: str | None = None  # workspace-relative .mp4 once rendered (None in stub mode)
    render_note: str | None = None
    # post payload
    caption: str | None = None
    hashtags: list[str] = []
    # shared
    artifacts: list[str] = []  # workspace-relative paths (storyboard.json, image, voiceover, manifest)
    publish_results: list[PublishResult] = []
    created_at: str
    note: str | None = None


class ReelRequest(CamelModel):
    brief: str
    targets: list[ReelTarget] | None = None
    # Unset -> inferred from the brief's script (a Devanagari brief drafts in Hindi), else English.
    language: ContentLanguage | None = None


class PostRequest(CamelModel):
    brief: str
    targets: list[PostTarget] | None = None
    language: ContentLanguage | None = None


class SocialDecision(CamelModel):
    action: Literal["approve", "reject"]
    note: str | None = None
