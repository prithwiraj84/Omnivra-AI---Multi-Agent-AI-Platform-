"""DocumentService — draft a document from a prompt, render to a chosen format,
gate on human approval (cp-0025).

The documentation agent (Gemma) writes a structured {title, sections} document; it
is rendered to PPTX / DOCX / PDF (doc_render, stub-safe -> markdown without the libs)
and persisted as a downloadable workspace artifact. Parsing falls back to a
deterministic builder so it runs fully offline.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from uuid import uuid4

from app.agents.runner import run_agent
from app.core.logging import logger
from app.providers.registry import get_provider_registry
from app.schemas.documents import DocChart, DocSection, DocSeries, DocTable, DocumentDraft
from app.services.artifacts import get_artifact_service
from app.services.doc_render import THEMES, render_document
from app.services.realtime import emit
from app.services.document_store import get_document_store
from app.workspace_fs.paths import project_root, safe_project_id

_EXT = {"pptx": "pptx", "docx": "docx", "pdf": "pdf"}
_DEFAULT_THEME = "indigo"


def _resolve_theme(requested: str | None, suggested: str | None = None) -> str:
    """Pick the visual theme: an explicit (non-'auto') request wins; else the agent's
    suggestion; else the default. Always returns a known palette name."""
    req = (requested or "").strip().lower()
    if req and req != "auto" and req in THEMES:
        return req
    sug = (suggested or "").strip().lower()
    if sug in THEMES:
        return sug
    return _DEFAULT_THEME


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DocumentService:
    def begin_document(self, prompt: str, fmt: str, theme: str, project_id: str | None) -> DocumentDraft:
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
            subtitle="", theme=_resolve_theme(theme), status="generating", sections=[], artifacts=[],
            file_path=None, stub=False, render_note=None, created_at=_now(),
        )
        get_document_store(pid).save(draft)
        return draft

    async def generate_document(self, doc_id: str, prompt: str, fmt: str, theme: str, project_id: str | None) -> None:
        """Background job: write the content (Gemma) + render the file, then move the draft to
        'awaiting_approval'. Never raises — on any error the draft still reaches a terminal state
        (so the UI poll never spins forever)."""
        pid = safe_project_id(project_id)
        fmt = fmt if fmt in _EXT else "pdf"
        store = get_document_store(pid)
        existing = store.get(doc_id)
        created_at = existing.created_at if existing else _now()  # keep stable list ordering
        written: list[str] = []  # files actually written so far — so the except-branch keeps them (no orphans)
        try:
            title, subtitle, resolved_theme, sections, content_note = await self._build_content(prompt, theme, fmt)

            base = f"reports/documents/{doc_id}"
            fm = get_artifact_service(pid).fm
            content_json = {"title": title, "subtitle": subtitle, "theme": resolved_theme, "sections": [s.model_dump() for s in sections]}
            written.append(fm.write_text(f"{base}/content.json", json.dumps(content_json, indent=2), agent_id="documentation-agent").rel_path)

            # Render the real file (or fall back to a markdown deliverable).
            out_rel = f"{base}/document.{_EXT[fmt]}"
            result = render_document(
                title, [s.model_dump() for s in sections], project_root(pid) / out_rel, fmt,
                subtitle=subtitle, theme=resolved_theme,
            )
            if result.get("ok") and not result.get("stub"):
                file_path: str | None = out_rel
                stub = False
                written.append(out_rel)
            else:
                md_rel = f"{base}/document.md"
                fm.write_text(md_rel, self._markdown(title, subtitle, sections), agent_id="documentation-agent")
                written.append(md_rel)
                file_path = md_rel
                stub = True

            # Surface the content-fallback notice (if any) ahead of the render-engine note.
            render_note = " ".join(n for n in (content_note, result.get("note")) if n) or None
            store.save(DocumentDraft(
                id=doc_id, project_id=pid, prompt=prompt, format=fmt, title=title, subtitle=subtitle,
                theme=resolved_theme, status="awaiting_approval", sections=sections, artifacts=written,
                file_path=file_path, stub=stub, render_note=render_note, created_at=created_at,
            ))
            await emit("approval", {"approvalId": doc_id, "title": "Document approval required", "kind": "document_publish", "requestedBy": "documentation-agent", "priority": "medium"})
        except Exception as exc:  # noqa: BLE001 - reach a terminal state, never leave it 'generating'
            logger.error("document generation failed for {}: {}", doc_id, repr(exc))
            try:  # the terminal save itself must not raise out of the BackgroundTask (would orphan 'generating')
                store.save(DocumentDraft(
                    id=doc_id, project_id=pid, prompt=prompt, format=fmt,
                    title=(prompt.strip()[:80] or "Document"), subtitle="", theme=_resolve_theme(theme),
                    status="awaiting_approval", sections=[],
                    artifacts=written or (existing.artifacts if existing else []),
                    file_path=None, stub=True, render_note=f"Generation error: {type(exc).__name__}", created_at=created_at,
                ))
            except Exception:  # noqa: BLE001 - last resort; nothing more we can do but log
                logger.error("terminal save for document {} also failed", doc_id)

    async def _build_content(self, prompt: str, theme: str, fmt: str = "pdf") -> tuple[str, str, str, list[DocSection], str | None]:
        """Return (title, subtitle, theme, sections, fallback_note). fallback_note is None when the
        model wrote real content; otherwise it explains why this is a placeholder (so the caller can
        surface it instead of silently serving generic boilerplate). ``fmt`` tailors the guidance
        (a deck wants concise, visual slides; a document allows richer prose)."""
        if fmt == "pptx":
            format_rule = (
                "- This is a PRESENTATION (slides): keep each section to a punchy heading, a SHORT body line, and "
                "3-5 concise bullets (a few words each, NOT paragraphs). Use a chart ONLY if the section genuinely "
                "has numeric data; most slides need none."
            )
        else:
            format_rule = (
                "- This is a written document. Use complete paragraphs of real sentences for each `body`, with "
                "bullets/tables/charts only where they genuinely add value."
            )
        ask = (
            "Write COMPLETE, professional documentation that DIRECTLY answers the request below. "
            "Respond with ONLY valid JSON (no markdown, no code fences, no commentary) in exactly this shape:\n"
            '{"title": str, "subtitle": str, "theme": str, "sections": [{"heading": str, "body": str, '
            '"bullets": [str], "table": {"headers": [str], "rows": [[str]]}, '
            '"chart": {"type": "column|bar|line|pie|area", "title": str, "categories": [str], '
            '"series": [{"name": str, "values": [number]}]}}]}\n'
            "Rules:\n"
            "- Stay STRICTLY on the requested topic. Write the actual content the user asked for — concrete, "
            "specific, and accurate (real steps, commands, examples as appropriate). Do NOT add generic filler, "
            "meta-commentary, or sections unrelated to the request.\n"
            "- Use as many sections as the topic genuinely needs (usually 4-9); no placeholders, no 'TODO', no '...'.\n"
            f"{format_rule}\n"
            "- DECIDE, per section, whether a table or chart is ACTUALLY warranted. MANY documents (guides, "
            "how-tos, tutorials, essays, policies, conceptual or narrative topics) need NO tables and NO charts at "
            "all — for those, write prose + bullets and OMIT table and chart entirely (use [] / leave them out). "
            "NEVER add a table or chart for decoration, to look thorough, or to fill space. Default to NOT including "
            "them; include one only when it conveys something prose/bullets genuinely cannot.\n"
            "- `bullets`: include ONLY where a list is the natural format; otherwise use [].\n"
            "- `table`: include ONLY for genuinely tabular content (option/flag references, side-by-side "
            "comparisons, config keys, schedules, specs). Omit it for everything else.\n"
            "- `chart`: include ONLY when the section contains REAL quantitative data inherent to the topic "
            "(measured trends, counts, percentages, comparisons). NEVER invent, estimate, or guess numbers just to "
            "draw a chart — if the topic is qualitative/instructional, use NO chart. Pie for parts-of-a-whole, "
            "line/area for trends, column/bar for comparisons. At most one chart per section.\n"
            '- Pick a `theme` whose mood fits the topic from EXACTLY this list: ["indigo","emerald","amber",'
            '"violet","slate","crimson","teal","ocean","sunset","forest","midnight","rose"] '
            "(e.g. finance/corporate -> slate/ocean/midnight; growth/eco/health -> emerald/forest/teal; "
            "marketing/creative -> sunset/violet/rose/crimson; technical -> indigo/teal/ocean).\n"
            "- Output the ENTIRE JSON and close every brace and bracket.\n"
            f"Request: {prompt}"
        )
        # Generous budget so a full doc fits; truncated JSON is still recovered by _parse.
        out = await run_agent("documentation-agent", ask, registry=get_provider_registry(), max_tokens=4096)
        if out.get("ok"):
            parsed = self._parse(out.get("content", ""))
            if parsed:
                title, subtitle, suggested, sections = parsed
                return title, subtitle, _resolve_theme(theme, suggested), sections, None
        # The model produced nothing usable (no/expired key, rate limit, or unparseable output).
        # Return an HONEST notice — never fabricate topic content that misleads the user.
        title, subtitle, sections = self._fallback(prompt)
        note = (
            "The documentation AI did not return content, so this is a placeholder notice — not generated "
            "documentation. The model is likely rate-limited or its free daily quota is exhausted; try again "
            "later or switch the document model in Settings."
        )
        return title, subtitle, _resolve_theme(theme), sections, note

    @staticmethod
    def _parse(text: str) -> tuple[str, str, str, list[DocSection]] | None:
        data = DocumentService._loads_document(text)
        if not data:
            return None
        title = str(data.get("title", "")).strip()
        subtitle = str(data.get("subtitle", "")).strip()
        suggested = str(data.get("theme", "")).strip()
        raw_sections = data.get("sections", [])
        if not isinstance(raw_sections, list):  # guard a malformed (non-list) sections value
            raw_sections = []
        sections: list[DocSection] = []
        for s in raw_sections:
            if not isinstance(s, dict):
                continue
            heading = str(s.get("heading", "")).strip()
            if not heading:
                continue
            bullets = [str(b).strip() for b in (s.get("bullets") or []) if str(b).strip()]
            sections.append(DocSection(
                heading=heading,
                body=str(s.get("body", "")).strip(),
                bullets=bullets,
                table=DocumentService._parse_table(s.get("table")),
                chart=DocumentService._parse_chart(s.get("chart")),
            ))
        return (title, subtitle, suggested, sections) if title and sections else None

    @staticmethod
    def _loads_document(text: str) -> dict | None:
        """Parse the model's JSON document. If the response is TRUNCATED (a long doc that ran past
        the token budget), salvage the head fields + every COMPLETE section object — so a cut-off
        response still yields a full document instead of collapsing to the tiny fallback."""
        if not text or "{" not in text:
            return None
        body = text[text.index("{"):]
        try:  # fast path: a well-formed, complete response
            return json.loads(body[: body.rindex("}") + 1])
        except Exception:  # noqa: BLE001 - truncated / trailing prose -> lenient recovery below
            pass
        title = DocumentService._scalar(body, "title")
        if not title:
            return None
        sections: list = []
        sidx = body.find('"sections"')
        if sidx != -1:
            lb = body.find("[", sidx)
            if lb != -1:
                sections = DocumentService._extract_objects(body[lb + 1:])
        return {
            "title": title,
            "subtitle": DocumentService._scalar(body, "subtitle"),
            "theme": DocumentService._scalar(body, "theme"),
            "sections": sections,
        }

    @staticmethod
    def _scalar(text: str, key: str) -> str:
        """Pull a top-level string field's value out of (possibly truncated) JSON, unescaped."""
        m = re.search(r'"' + re.escape(key) + r'"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
        if not m:
            return ""
        try:
            return json.loads('"' + m.group(1) + '"')  # unescape \n, \" etc.
        except Exception:  # noqa: BLE001
            return m.group(1)

    @staticmethod
    def _extract_objects(s: str) -> list[dict]:
        """Extract each COMPLETE top-level {...} object from a (maybe truncated) JSON array body,
        parsing them individually. A trailing incomplete object is simply skipped (not appended)."""
        objs: list[dict] = []
        depth = 0
        start: int | None = None
        in_str = False
        esc = False
        for i, ch in enumerate(s):
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        try:
                            obj = json.loads(s[start : i + 1])
                            if isinstance(obj, dict):
                                objs.append(obj)
                        except Exception:  # noqa: BLE001 - skip a malformed object
                            pass
                        start = None
            elif ch == "]" and depth == 0:
                break  # end of the sections array
        return objs

    @staticmethod
    def _parse_table(raw: object) -> DocTable | None:
        """Coerce a model-emitted table into a DocTable, or None if there's nothing tabular."""
        if not isinstance(raw, dict):
            return None
        headers = [str(h).strip() for h in (raw.get("headers") or [])]
        rows = [[str(c).strip() for c in row] for row in (raw.get("rows") or []) if isinstance(row, (list, tuple))]
        rows = [r for r in rows if any(c for c in r)]  # drop fully-empty rows (no tabular content)
        if not headers and not rows:  # nothing tabular left -> not a table
            return None
        return DocTable(headers=headers, rows=rows)

    @staticmethod
    def _parse_chart(raw: object) -> DocChart | None:
        """Coerce a model-emitted chart into a DocChart, or None when there's no usable numeric data."""
        if not isinstance(raw, dict):
            return None
        ctype = str(raw.get("type", "column")).strip().lower()
        if ctype not in {"column", "bar", "line", "pie", "area"}:
            ctype = "column"
        categories = [str(c).strip() for c in (raw.get("categories") or [])]
        series: list[DocSeries] = []
        for s in (raw.get("series") or []):
            if not isinstance(s, dict):
                continue
            values: list[float] = []
            parsed_any = False  # require at least one genuinely-numeric value to keep the series
            for v in (s.get("values") or []):
                try:
                    f = float(str(v).replace(",", "").replace("$", "").replace("%", ""))
                except (TypeError, ValueError):
                    values.append(0.0)
                    continue
                if math.isfinite(f):
                    values.append(f)
                    parsed_any = True
                else:  # inf/nan would break the chart's worksheet writer
                    values.append(0.0)
            if values and parsed_any:
                series.append(DocSeries(name=str(s.get("name", "")).strip(), values=values))
        if not series:  # no genuinely-numeric data -> not a chart
            return None
        return DocChart(type=ctype, title=str(raw.get("title", "")).strip(), categories=categories, series=series)

    @staticmethod
    def _fallback(prompt: str) -> tuple[str, str, list[DocSection]]:
        """HONEST placeholder used ONLY when the documentation model returns nothing usable (no key /
        rate-limited / unparseable). It does NOT fabricate topic content (which would be irrelevant to
        the request) and adds NO table — it plainly says the content could not be generated and why,
        titled by the user's request so the draft stays on-topic."""
        topic = (prompt.strip()[:120] or "your request")
        title = prompt.strip()[:80] or "Document"
        sections = [
            DocSection(
                heading="Content could not be generated",
                body=(
                    f'Omnivra could not generate the document for "{topic}" because the documentation AI model '
                    "did not return any content. This is a temporary provider issue rather than a problem with "
                    "your request, and no topic content was written for this draft."
                ),
                bullets=[
                    "Most often the configured model is rate-limited or its free daily quota is exhausted",
                    "Try again in a few minutes, or switch the document model in Settings to an available provider",
                    "Your prompt and chosen format were saved, so regenerating will reuse them",
                ],
            ),
        ]
        return title, "Draft could not be completed", sections

    @staticmethod
    def _markdown(title: str, subtitle: str, sections: list[DocSection]) -> str:
        lines = [f"# {title}", ""]
        if subtitle:
            lines += [f"_{subtitle}_", ""]
        for s in sections:
            lines += [f"## {s.heading}", ""]
            if s.body:
                lines += [s.body, ""]
            for b in s.bullets:
                lines.append(f"- {b}")
            if s.bullets:
                lines.append("")
            if s.table and (s.table.headers or s.table.rows):
                headers = s.table.headers or [""] * (max((len(r) for r in s.table.rows), default=1))
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join("---" for _ in headers) + " |")
                for row in s.table.rows:
                    padded = (row + [""] * len(headers))[: len(headers)]
                    lines.append("| " + " | ".join(padded) + " |")
                lines.append("")
            if s.chart and s.chart.series:  # render a chart's data as a markdown table
                cats = s.chart.categories or [str(i + 1) for i in range(max((len(se.values) for se in s.chart.series), default=0))]
                lines.append(f"**{s.chart.title or s.chart.type.title() + ' chart'}**")
                head = ["Category"] + [se.name or f"Series {i+1}" for i, se in enumerate(s.chart.series)]
                lines.append("| " + " | ".join(head) + " |")
                lines.append("| " + " | ".join("---" for _ in head) + " |")
                for i, cat in enumerate(cats):
                    vals = [(f"{se.values[i]:g}" if i < len(se.values) else "") for se in s.chart.series]
                    lines.append("| " + " | ".join([cat] + vals) + " |")
                lines.append("")
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
