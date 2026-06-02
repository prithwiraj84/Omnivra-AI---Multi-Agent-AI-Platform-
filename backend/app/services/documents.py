"""DocumentService — draft a document from a prompt, render to a chosen format,
gate on human approval (cp-0025).

The documentation agent (Gemma) writes a structured {title, sections} document; it
is rendered to PPTX / DOCX / PDF (doc_render, stub-safe -> markdown without the libs)
and persisted as a downloadable workspace artifact. Parsing falls back to a
deterministic builder so it runs fully offline.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from app.agents.runner import run_agent
from app.core.logging import logger
from app.providers.registry import get_provider_registry
from app.schemas.documents import DocSection, DocumentDraft
from app.services.artifacts import get_artifact_service
from app.services.doc_render import render_document
from app.services.realtime import emit
from app.services.document_store import get_document_store
from app.workspace_fs.paths import project_root, safe_project_id

_EXT = {"pptx": "pptx", "docx": "docx", "pdf": "pdf"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DocumentService:
    def begin_document(self, prompt: str, fmt: str, project_id: str | None) -> DocumentDraft:
        """Persist a 'generating' placeholder + return it IMMEDIATELY (fire-and-poll).

        The model write + render (which can take many seconds — well past the UI request timeout
        when a provider is rate-limited) runs in the background via :meth:`generate_document`, which
        overwrites this record. The client polls GET /api/documents until status != 'generating'.
        This is what stops Document Studio's 'Could not generate the document' timeout.
        """
        pid = safe_project_id(project_id)
        fmt = fmt if fmt in _EXT else "pdf"
        doc_id = "doc_" + uuid4().hex[:12]
        draft = DocumentDraft(
            id=doc_id, project_id=pid, prompt=prompt, format=fmt, title="Generating…",
            status="generating", sections=[], artifacts=[], file_path=None, stub=False,
            render_note=None, created_at=_now(),
        )
        get_document_store(pid).save(draft)
        return draft

    async def generate_document(self, doc_id: str, prompt: str, fmt: str, project_id: str | None) -> None:
        """Background job: write the content (Gemma) + render the file, then move the draft to
        'awaiting_approval'. Never raises — on any error the draft still reaches a terminal state
        (so the UI poll never spins forever)."""
        pid = safe_project_id(project_id)
        fmt = fmt if fmt in _EXT else "pdf"
        store = get_document_store(pid)
        existing = store.get(doc_id)
        created_at = existing.created_at if existing else _now()  # keep stable list ordering
        try:
            title, sections = await self._build_content(prompt)

            base = f"reports/documents/{doc_id}"
            fm = get_artifact_service(pid).fm
            artifacts: list[str] = [
                fm.write_text(f"{base}/content.json", json.dumps({"title": title, "sections": [s.model_dump() for s in sections]}, indent=2), agent_id="documentation-agent").rel_path,
            ]

            # Render the real file (or fall back to a markdown deliverable).
            out_rel = f"{base}/document.{_EXT[fmt]}"
            result = render_document(title, [s.model_dump() for s in sections], project_root(pid) / out_rel, fmt)
            if result.get("ok") and not result.get("stub"):
                file_path: str | None = out_rel
                stub = False
                artifacts.append(out_rel)
            else:
                md_rel = f"{base}/document.md"
                fm.write_text(md_rel, self._markdown(title, sections), agent_id="documentation-agent")
                artifacts.append(md_rel)
                file_path = md_rel
                stub = True

            store.save(DocumentDraft(
                id=doc_id, project_id=pid, prompt=prompt, format=fmt, title=title,
                status="awaiting_approval", sections=sections, artifacts=artifacts,
                file_path=file_path, stub=stub, render_note=result.get("note"), created_at=created_at,
            ))
            await emit("approval", {"approvalId": doc_id, "title": "Document approval required", "kind": "document_publish", "requestedBy": "documentation-agent", "priority": "medium"})
        except Exception as exc:  # noqa: BLE001 - reach a terminal state, never leave it 'generating'
            logger.error("document generation failed for {}: {}", doc_id, repr(exc))
            try:  # the terminal save itself must not raise out of the BackgroundTask (would orphan 'generating')
                store.save(DocumentDraft(
                    id=doc_id, project_id=pid, prompt=prompt, format=fmt,
                    title=(prompt.strip()[:80] or "Document"), status="awaiting_approval",
                    sections=[], artifacts=existing.artifacts if existing else [], file_path=None, stub=True,
                    render_note=f"Generation error: {type(exc).__name__}", created_at=created_at,
                ))
            except Exception:  # noqa: BLE001 - last resort; nothing more we can do but log
                logger.error("terminal save for document {} also failed", doc_id)

    async def _build_content(self, prompt: str) -> tuple[str, list[DocSection]]:
        ask = (
            "Write a structured document for this request. Respond ONLY with JSON of the form "
            '{"title","sections":[{"heading","body"}]} with 3-6 sections. '
            f"Request: {prompt}"
        )
        out = await run_agent("documentation-agent", ask, registry=get_provider_registry(), max_tokens=900)
        if out.get("ok"):
            parsed = self._parse(out.get("content", ""))
            if parsed:
                return parsed
        return self._fallback(prompt)

    @staticmethod
    def _parse(text: str) -> tuple[str, list[DocSection]] | None:
        try:
            data = json.loads(text[text.index("{") : text.rindex("}") + 1])
            title = str(data.get("title", "")).strip()
            sections = [
                DocSection(heading=str(s.get("heading", "")).strip(), body=str(s.get("body", "")).strip())
                for s in data.get("sections", [])
                if str(s.get("heading", "")).strip()
            ]
            return (title, sections) if title and sections else None
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _fallback(prompt: str) -> tuple[str, list[DocSection]]:
        title = prompt.strip()[:80] or "Untitled Document"
        sections = [
            DocSection(heading="Overview", body=f"This document covers: {prompt.strip()}."),
            DocSection(heading="Key Points", body="Generated by the Omnivra documentation agent. Provider keys enable richer, model-written content."),
            DocSection(heading="Details", body="Replace this with the model's output once a provider key is configured."),
            DocSection(heading="Next Steps", body="Review and approve this draft, then download it in the chosen format."),
        ]
        return title, sections

    @staticmethod
    def _markdown(title: str, sections: list[DocSection]) -> str:
        lines = [f"# {title}", ""]
        for s in sections:
            lines += [f"## {s.heading}", "", s.body, ""]
        lines += ["---", "_Install the render engine (pip install -r requirements-docs.txt) for a real PPTX/DOCX/PDF._"]
        return "\n".join(lines)

    async def decide(self, doc_id: str, action: str, note: str | None, project_id: str | None) -> DocumentDraft | None:
        pid = safe_project_id(project_id)
        store = get_document_store(pid)
        draft = store.get(doc_id)
        if draft is None:
            return None
        draft.status = "approved" if action == "approve" else "rejected"
        draft.note = note
        store.save(draft)
        await emit("workflow", {"workflowId": doc_id, "projectId": pid, "status": draft.status, "kind": "document"})
        return draft


_service = DocumentService()


def get_document_service() -> DocumentService:
    return _service
