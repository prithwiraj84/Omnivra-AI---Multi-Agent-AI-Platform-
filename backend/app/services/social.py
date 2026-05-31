"""SocialService — draft reels/posts, gate on human approval, then publish (stub).

Phase 1 (cp-0016) is offline/stub-first: the reel-automation / social-strategist
agents draft a structured storyboard (reel) or caption+tags (post); media comes
from the stub-safe MediaService (FLUX image, Orpheus voiceover placeholder); a
manifest + storyboard are persisted as path-jailed artifacts in the project
workspace; the draft awaits human approval; on approve it "publishes" to each
target via the stub publishers. Real video render + real uploads land in later
phases. Parsing falls back to a deterministic builder so it runs fully offline.
"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.agents.runner import run_agent
from app.core.logging import logger
from app.providers.registry import get_provider_registry
from app.schemas.social import (
    DEFAULT_POST_TARGETS,
    DEFAULT_REEL_TARGETS,
    PublishResult,
    ReelScene,
    ReelStoryboard,
    SocialDraft,
)
from app.services.artifacts import get_artifact_service
from app.services.media import get_media_service
from app.services.pexels import fetch_broll
from app.services.publishers import publish_to
from app.services.realtime import emit
from app.services.reel_render import render_reel
from app.services.social_store import get_social_store
from app.workspace_fs.paths import project_root, safe_project_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _keywords(brief: str, n: int = 6) -> list[str]:
    out: list[str] = []
    for w in re.findall(r"[A-Za-z0-9]+", brief.lower()):
        if len(w) > 3 and w not in out:
            out.append(w)
        if len(out) >= n:
            break
    return out or ["brand"]


class SocialService:
    # ---- reel -------------------------------------------------------------
    async def draft_reel(self, brief: str, targets: list[str] | None, project_id: str | None) -> SocialDraft:
        pid = safe_project_id(project_id)
        draft_id = "reel_" + uuid4().hex[:12]
        storyboard = await self._build_storyboard(brief)

        fm = get_artifact_service(pid).fm
        base = f"reports/social/{draft_id}"
        artifacts: list[str] = [
            fm.write_text(f"{base}/storyboard.json", storyboard.model_dump_json(by_alias=True, indent=2), agent_id="reel-automation").rel_path,
            fm.write_text(f"{base}/reel.md", self._reel_manifest(brief, storyboard), agent_id="reel-automation").rel_path,
        ]
        # Stub voiceover for the hook (real Orpheus TTS wiring lands later).
        vo = await get_media_service().synthesize(storyboard.hook or brief, pid)
        if vo.get("path"):
            artifacts.append(vo["path"])

        draft = SocialDraft(
            id=draft_id, project_id=pid, kind="reel", brief=brief,
            status="awaiting_approval", targets=targets or DEFAULT_REEL_TARGETS,
            storyboard=storyboard, artifacts=artifacts, created_at=_now(),
        )
        get_social_store(pid).save(draft)
        await self._emit_pending(draft)
        return draft

    async def _build_storyboard(self, brief: str) -> ReelStoryboard:
        prompt = (
            "Plan a 30-second vertical short-form reel for this brief. Respond ONLY with JSON of the form "
            '{"title","hook","scenes":[{"durationSec","voiceover","brollQuery","onScreenText"}],"musicMood","callToAction"}. '
            f"Brief: {brief}"
        )
        out = await run_agent("reel-automation", prompt, registry=get_provider_registry(), max_tokens=700)
        parsed = self._parse_storyboard(out.get("content", "")) if out.get("ok") else None
        return parsed or self._fallback_storyboard(brief)

    @staticmethod
    def _parse_storyboard(text: str) -> ReelStoryboard | None:
        try:
            data = json.loads(text[text.index("{") : text.rindex("}") + 1])
            sb = ReelStoryboard.model_validate(data)
            if not sb.scenes:
                return None
            sb.total_duration_sec = round(sum(s.duration_sec for s in sb.scenes), 1)
            return sb
        except Exception:  # noqa: BLE001 - any parse failure -> deterministic fallback
            return None

    @staticmethod
    def _fallback_storyboard(brief: str) -> ReelStoryboard:
        kw = _keywords(brief)
        beats = [
            ("Hook: stop the scroll", f"Here's how {brief.strip()[:60]} changes everything."),
            ("The problem", "Most teams still do this the slow, manual way."),
            ("The shift", "Omnivra's AI company handles it end to end."),
            ("Proof", "Faster output, fewer errors — with human approval on every step."),
            ("Call to action", "Follow to see your AI workforce in action."),
        ]
        scenes = [
            ReelScene(duration_sec=5.0, voiceover=vo, broll_query=" ".join(kw[i : i + 2]) or "technology", on_screen_text=ost)
            for i, (ost, vo) in enumerate(beats)
        ]
        return ReelStoryboard(
            title=brief.strip()[:70] or "Untitled reel",
            hook=beats[0][1],
            scenes=scenes,
            music_mood="upbeat",
            call_to_action="Follow for more.",
            total_duration_sec=round(sum(s.duration_sec for s in scenes), 1),
        )

    @staticmethod
    def _reel_manifest(brief: str, sb: ReelStoryboard) -> str:
        lines = [
            f"# Reel draft — {sb.title}", "",
            f"**Brief:** {brief}", f"**Hook:** {sb.hook}", f"**Music:** {sb.music_mood}",
            f"**Duration:** ~{sb.total_duration_sec:.0f}s", f"**CTA:** {sb.call_to_action}", "", "## Scenes", "",
        ]
        for i, s in enumerate(sb.scenes, 1):
            lines += [
                f"### Scene {i} ({s.duration_sec:.0f}s)",
                f"- **Voiceover:** {s.voiceover}",
                f"- **B-roll (Pexels):** {s.broll_query}",
                f"- **On-screen:** {s.on_screen_text}", "",
            ]
        lines += ["---", "_Storyboard is render-ready. Video assembly (MoviePy + Pexels + Orpheus) lands in a later phase._"]
        return "\n".join(lines)

    # ---- post -------------------------------------------------------------
    async def draft_post(self, brief: str, targets: list[str] | None, project_id: str | None) -> SocialDraft:
        pid = safe_project_id(project_id)
        draft_id = "post_" + uuid4().hex[:12]
        caption, hashtags = await self._build_caption(brief)

        img = await get_media_service().generate_image(self._image_prompt(brief), pid)
        artifacts: list[str] = [img["path"]] if img.get("path") else []
        fm = get_artifact_service(pid).fm
        body = f"# Post draft\n\n**Brief:** {brief}\n\n## Caption\n\n{caption}\n\n## Hashtags\n\n{' '.join(hashtags)}\n"
        artifacts.append(fm.write_text(f"reports/social/{draft_id}/post.md", body, agent_id="social-strategist").rel_path)

        draft = SocialDraft(
            id=draft_id, project_id=pid, kind="post", brief=brief,
            status="awaiting_approval", targets=targets or DEFAULT_POST_TARGETS,
            caption=caption, hashtags=hashtags, artifacts=artifacts, created_at=_now(),
        )
        get_social_store(pid).save(draft)
        await self._emit_pending(draft)
        return draft

    async def _build_caption(self, brief: str) -> tuple[str, list[str]]:
        prompt = (
            'Write a social post for this brief. Respond ONLY with JSON {"caption","hashtags":[...]}. '
            f"Brief: {brief}"
        )
        out = await run_agent("social-strategist", prompt, registry=get_provider_registry(), max_tokens=400)
        if out.get("ok"):
            parsed = self._parse_caption(out.get("content", ""))
            if parsed:
                return parsed
        return self._fallback_caption(brief)

    @staticmethod
    def _parse_caption(text: str) -> tuple[str, list[str]] | None:
        try:
            data = json.loads(text[text.index("{") : text.rindex("}") + 1])
            caption = str(data.get("caption", "")).strip()
            tags = [f"#{str(t).lstrip('#')}" for t in data.get("hashtags", []) if str(t).strip()]
            return (caption, tags) if caption else None
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _fallback_caption(brief: str) -> tuple[str, list[str]]:
        caption = f"{brief.strip()[:180]}\n\nBuilt by Omnivra — your autonomous AI company. Human-approved, every time."
        tags = [f"#{w}" for w in _keywords(brief, 5)] + ["#AI", "#Automation", "#Omnivra"]
        return caption, tags

    @staticmethod
    def _image_prompt(brief: str) -> str:
        return f"High-quality social media marketing image for: {brief}. Clean, modern, brand-forward, vibrant."

    # ---- decision / publish ----------------------------------------------
    async def decide(self, draft_id: str, action: str, note: str | None, project_id: str | None) -> SocialDraft | None:
        pid = safe_project_id(project_id)
        store = get_social_store(pid)
        draft = store.get(draft_id)
        if draft is None:
            return None
        if action == "reject":
            draft.status = "rejected"
            draft.note = note
        else:  # approve -> publish to each target (YouTube real; others stub)
            draft.publish_results = [await publish_to(platform, draft) for platform in draft.targets]
            draft.status = "published"
            draft.note = note
            await emit("workflow", {"workflowId": draft.id, "projectId": pid, "status": "published", "kind": draft.kind})
        store.save(draft)
        return draft

    # ---- render (reels) ---------------------------------------------------
    def begin_render(self, draft_id: str, project_id: str | None) -> SocialDraft | None:
        """Mark a reel draft as rendering (synchronous). Returns the draft, or None if
        it doesn't exist / isn't a renderable reel."""
        pid = safe_project_id(project_id)
        store = get_social_store(pid)
        draft = store.get(draft_id)
        # Only render a reel that is still awaiting approval — never one already
        # published/rejected (prevents a render racing a concurrent decision).
        if draft is None or draft.kind != "reel" or draft.storyboard is None or draft.status != "awaiting_approval":
            return None
        draft.render_status = "rendering"
        draft.render_note = None
        store.save(draft)
        return draft

    async def run_render(self, draft_id: str, project_id: str | None) -> None:
        """Background job: gather b-roll + voiceover, render the .mp4 off the event loop,
        and update the draft's render status. Never raises (records 'failed' instead)."""
        pid = safe_project_id(project_id)
        store = get_social_store(pid)
        draft = store.get(draft_id)
        # Always reach a terminal state — never leave a draft stuck on 'rendering'.
        if draft is None:
            # Vanished between begin_render and here (e.g. project purged); emit terminal, don't recreate.
            await emit("workflow", {"workflowId": draft_id, "projectId": pid, "status": "failed", "kind": "reel"})
            return
        if draft.storyboard is None:
            draft.render_status = "failed"
            draft.render_note = "No storyboard to render."
            store.save(draft)
            await emit("workflow", {"workflowId": draft_id, "projectId": pid, "status": "failed", "kind": "reel"})
            return
        await emit("workflow", {"workflowId": draft_id, "projectId": pid, "status": "rendering", "kind": "reel"})
        try:
            scenes = draft.storyboard.scenes
            media_dir = project_root(pid) / "reports" / "media" / draft_id
            # B-roll per scene (best-effort, concurrent; None -> color background).
            broll = list(await asyncio.gather(*[fetch_broll(s.broll_query, media_dir / f"broll_{i}.mp4") for i, s in enumerate(scenes)]))
            vo_text = " ".join(s.voiceover for s in scenes if s.voiceover).strip()
            vo_rel = await get_media_service().generate_voiceover(vo_text, pid) if vo_text else None
            vo_path = project_root(pid) / vo_rel if vo_rel else None

            out_rel = f"reports/social/{draft_id}/reel.mp4"
            result = await asyncio.to_thread(
                render_reel, draft.storyboard, project_root(pid) / out_rel, broll=broll, voiceover=vo_path
            )

            draft = store.get(draft_id) or draft  # re-read latest
            if result.get("ok") and not result.get("stub"):
                draft.render_status = "rendered"
                draft.video_path = out_rel
                if out_rel not in draft.artifacts:
                    draft.artifacts.append(out_rel)
                draft.render_note = "Rendered a real .mp4" + (" with voiceover." if vo_path else " (silent — set HUGGINGFACE_API_KEY for Orpheus TTS).")
            elif result.get("stub"):
                draft.render_status = "rendered"  # storyboard is the deliverable without the engine
                draft.video_path = None
                draft.render_note = result.get("note", "Render engine not installed; storyboard saved.")
            else:
                draft.render_status = "failed"
                draft.render_note = result.get("note", "render failed")
            store.save(draft)
        except Exception as exc:  # noqa: BLE001 - never let a render crash the worker
            logger.error("run_render failed for {}: {}", draft_id, repr(exc))
            draft = store.get(draft_id) or draft
            draft.render_status = "failed"
            draft.render_note = f"{exc!r}"
            store.save(draft)
        await emit("workflow", {"workflowId": draft_id, "projectId": pid, "status": draft.render_status, "kind": "reel"})

    async def _emit_pending(self, draft: SocialDraft) -> None:
        await emit(
            "approval",
            {
                "approvalId": draft.id,
                "title": f"{draft.kind.title()} approval required",
                "kind": f"{draft.kind}_publish",
                "requestedBy": "reel-automation" if draft.kind == "reel" else "social-strategist",
                "priority": "high",
            },
        )


_service = SocialService()


def get_social_service() -> SocialService:
    """Process-wide SocialService (stateless; per-project stores are resolved per call)."""
    return _service
