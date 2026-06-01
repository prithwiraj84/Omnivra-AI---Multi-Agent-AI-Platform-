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


# Cap the draft-time hook-voiceover PREVIEW so the interactive POST can't hang on a slow
# Groq TTS call (the full narration is re-synthesized at render time, off the request path).
_DRAFT_TTS_TIMEOUT = 20.0


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
    # ---- live progress ----------------------------------------------------
    def _stepper(self, job: str, project_id: str, kind: str, phase: str, *, total: int):
        """Return an async ``step(...)`` that broadcasts a 'social_progress' frame for this job.

        Lets the Social Studio show live per-step progress (storyboard/voiceover for reels,
        caption/image for posts, Pexels b-roll/MoviePy assemble at render) BEFORE the
        human-approval view. Best-effort: ``emit`` is a no-op with no clients and never raises,
        so progress reporting can never break generation or render.
        """
        async def step(key: str, label: str, status: str, index: int, detail: str | None = None) -> None:
            await emit(
                "social_progress",
                {
                    "jobId": job, "projectId": project_id, "kind": kind, "phase": phase,
                    "step": key, "label": label, "status": status,
                    "index": index, "total": total, "detail": detail,
                },
            )

        return step

    # ---- reel -------------------------------------------------------------
    async def draft_reel(self, brief: str, targets: list[str] | None, project_id: str | None) -> SocialDraft:
        pid = safe_project_id(project_id)
        draft_id = "reel_" + uuid4().hex[:12]
        step = self._stepper(draft_id, pid, "reel", "draft", total=3)

        await step("storyboard", "Writing the storyboard…", "running", 1)
        storyboard = await self._build_storyboard(brief)
        await step("storyboard", "Storyboard ready", "done", 1, detail=f"{len(storyboard.scenes)} scenes · ~{storyboard.total_duration_sec:.0f}s")

        fm = get_artifact_service(pid).fm
        base = f"reports/social/{draft_id}"
        artifacts: list[str] = [
            fm.write_text(f"{base}/storyboard.json", storyboard.model_dump_json(by_alias=True, indent=2), agent_id="reel-automation").rel_path,
            fm.write_text(f"{base}/reel.md", self._reel_manifest(brief, storyboard), agent_id="reel-automation").rel_path,
        ]
        # A short hook-voiceover PREVIEW via Groq Orpheus (the full narration is re-synthesized
        # at render time). Time-boxed with wait_for so the interactive draft never blocks on a
        # slow/degraded TTS call — on timeout we just skip the preview (never raises).
        await step("voiceover", "Generating the hook voiceover…", "running", 2)
        try:
            vo = await asyncio.wait_for(get_media_service().synthesize(storyboard.hook or brief, pid), timeout=_DRAFT_TTS_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("Draft hook voiceover timed out after {}s; continuing without the preview", _DRAFT_TTS_TIMEOUT)
            vo = {}
        if vo.get("path"):
            artifacts.append(vo["path"])
        await step("voiceover", "Voiceover ready" if vo.get("path") and not vo.get("stub") else "Voiceover preview ready", "done", 2)

        draft = SocialDraft(
            id=draft_id, project_id=pid, kind="reel", brief=brief,
            status="awaiting_approval", targets=targets or DEFAULT_REEL_TARGETS,
            storyboard=storyboard, artifacts=artifacts, created_at=_now(),
        )
        get_social_store(pid).save(draft)
        await step("ready", "Ready for your review", "done", 3)
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
        lines += ["---", "_Storyboard is render-ready. Click Render to assemble the video (MoviePy + Pexels b-roll + Groq Orpheus voiceover)._"]
        return "\n".join(lines)

    # ---- post -------------------------------------------------------------
    async def draft_post(self, brief: str, targets: list[str] | None, project_id: str | None) -> SocialDraft:
        pid = safe_project_id(project_id)
        draft_id = "post_" + uuid4().hex[:12]
        step = self._stepper(draft_id, pid, "post", "draft", total=3)

        await step("caption", "Writing the caption & hashtags…", "running", 1)
        caption, hashtags = await self._build_caption(brief)
        await step("caption", "Caption ready", "done", 1, detail=f"{len(hashtags)} hashtags")

        await step("image", "Generating the post image (FLUX)…", "running", 2)
        img = await get_media_service().generate_image(self._image_prompt(brief), pid)
        artifacts: list[str] = [img["path"]] if img.get("path") else []
        await step("image", "Image ready" if img.get("path") else "Image step complete", "done", 2,
                   detail=None if img.get("path") else "set HUGGINGFACE_API_KEY for a real FLUX image")

        fm = get_artifact_service(pid).fm
        body = f"# Post draft\n\n**Brief:** {brief}\n\n## Caption\n\n{caption}\n\n## Hashtags\n\n{' '.join(hashtags)}\n"
        artifacts.append(fm.write_text(f"reports/social/{draft_id}/post.md", body, agent_id="social-strategist").rel_path)

        draft = SocialDraft(
            id=draft_id, project_id=pid, kind="post", brief=brief,
            status="awaiting_approval", targets=targets or DEFAULT_POST_TARGETS,
            caption=caption, hashtags=hashtags, artifacts=artifacts, created_at=_now(),
        )
        get_social_store(pid).save(draft)
        await step("ready", "Ready for your review", "done", 3)
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

    async def delete_draft(self, draft_id: str, project_id: str | None) -> bool:
        """Hard-delete a draft: its JSON record + all of its workspace artifacts. True if it existed.

        Best-effort on the files (a missing/locked artifact never blocks the delete); every
        removal is path-jailed by the FileManager. Lets the user discard a reel/post they
        don't like, reclaiming its storyboard / b-roll / rendered .mp4 / image / voiceover.
        """
        pid = safe_project_id(project_id)
        store = get_social_store(pid)
        draft = store.get(draft_id)
        if draft is None:
            return False
        fm = get_artifact_service(pid).fm
        # Each listed artifact (storyboard.json, reel.md/post.md, reel.mp4, image, voiceover)…
        for rel in list(draft.artifacts):
            try:
                fm.delete_path(rel)
            except Exception as exc:  # noqa: BLE001 - never let one stuck file block the delete
                logger.warning("Could not delete artifact {} for {}: {}", rel, draft_id, repr(exc))
        # …plus the per-draft folders (rendered output + downloaded b-roll).
        for d in (f"reports/social/{draft_id}", f"reports/media/{draft_id}"):
            try:
                fm.delete_path(d)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not delete dir {} for {}: {}", d, draft_id, repr(exc))
        store.delete(draft_id)
        await emit("workflow", {"workflowId": draft_id, "projectId": pid, "status": "deleted", "kind": draft.kind})
        return True

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
            store.save_if_exists(draft)  # don't resurrect if deleted meanwhile
            await emit("workflow", {"workflowId": draft_id, "projectId": pid, "status": "failed", "kind": "reel"})
            return
        rstep = self._stepper(draft_id, pid, "reel", "render", total=4)
        await emit("workflow", {"workflowId": draft_id, "projectId": pid, "status": "rendering", "kind": "reel"})
        saved = False
        try:
            scenes = draft.storyboard.scenes
            media_dir = project_root(pid) / "reports" / "media" / draft_id
            # B-roll per scene (best-effort, concurrent; None -> color background).
            await rstep("broll", "Gathering b-roll from Pexels…", "running", 1)
            broll = list(await asyncio.gather(*[fetch_broll(s.broll_query, media_dir / f"broll_{i}.mp4") for i, s in enumerate(scenes)]))
            got = sum(1 for b in broll if b)
            await rstep("broll", "B-roll gathered", "done", 1, detail=f"{got}/{len(scenes)} clips from Pexels" if got else "color backgrounds (set PEXELS_API_KEY for stock video)")

            # PER-SCENE voiceover so each scene's narration is in sync with its own b-roll +
            # caption (one combined track over fixed-length visuals drifts out of sync).
            await rstep("voiceover", "Synthesizing the voiceover (Orpheus)…", "running", 2)
            voiceovers: list[Path | None] = []
            vo_rels: list[str] = []
            vo_note = ""
            has_narration = any((s.voiceover or "").strip() for s in scenes)
            for sc in scenes:
                txt = (sc.voiceover or "").strip()
                if not txt:
                    voiceovers.append(None)
                    continue
                rel, note = await get_media_service().voiceover_with_note(txt, pid)
                if rel:
                    voiceovers.append(project_root(pid) / rel)
                    vo_rels.append(rel)
                else:
                    voiceovers.append(None)
                    vo_note = note  # remember the last reason (e.g. Groq terms / no key)
            vo_made = len(vo_rels)
            # Surface WHY there's no audio (e.g. Groq Orpheus terms acceptance) instead of a silent miss.
            await rstep(
                "voiceover",
                f"Voiceover ready ({vo_made}/{len(scenes)} scenes)" if vo_made else ("No narration" if not has_narration else "Voiceover failed"),
                "done" if (vo_made or not has_narration) else "error",
                2,
                detail=None if vo_made else (vo_note or "no narration in the storyboard"),
            )

            await rstep("assemble", "Assembling the video (MoviePy)…", "running", 3)
            out_rel = f"reports/social/{draft_id}/reel.mp4"
            result = await asyncio.to_thread(
                render_reel, draft.storyboard, project_root(pid) / out_rel, broll=broll, voiceovers=voiceovers
            )
            # render_reel RETURNS a failure (ok=False, stub=False) rather than raising, so the
            # assemble row must reflect the result — not be marked done unconditionally.
            assembled = bool(result.get("ok") or result.get("stub"))
            await rstep("assemble", "Video assembled" if assembled else "Assembly failed", "done" if assembled else "error", 3,
                        detail=None if assembled else (result.get("note") or "render failed"))

            draft = store.get(draft_id) or draft  # re-read latest
            # Track each scene's voiceover (flat reports/media/<uuid>.wav) so delete_draft reclaims them.
            for rel in vo_rels:
                if rel not in draft.artifacts:
                    draft.artifacts.append(rel)
            if result.get("ok") and not result.get("stub"):
                draft.render_status = "rendered"
                draft.video_path = out_rel
                if out_rel not in draft.artifacts:
                    draft.artifacts.append(out_rel)
                draft.render_note = "Rendered a real .mp4" + (" with voiceover." if vo_made else f" (silent — {vo_note or 'no narration'}).")
            elif result.get("stub"):
                draft.render_status = "rendered"  # storyboard is the deliverable without the engine
                draft.video_path = None
                draft.render_note = result.get("note", "Render engine not installed; storyboard saved.")
            else:
                draft.render_status = "failed"
                draft.render_note = result.get("note", "render failed")
            saved = store.save_if_exists(draft)
        except Exception as exc:  # noqa: BLE001 - never let a render crash the worker
            logger.error("run_render failed for {}: {}", draft_id, repr(exc))
            draft = store.get(draft_id) or draft
            draft.render_status = "failed"
            draft.render_note = f"{exc!r}"
            saved = store.save_if_exists(draft)
        # If the draft was DELETED mid-render, don't resurrect it — emit a terminal 'deleted' and stop.
        if not saved:
            await emit("workflow", {"workflowId": draft_id, "projectId": pid, "status": "deleted", "kind": "reel"})
            return
        # Terminal progress frame mirrors the draft's final render_status.
        await rstep("rendered", draft.render_note or draft.render_status, "done" if draft.render_status == "rendered" else "error", 4)
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
