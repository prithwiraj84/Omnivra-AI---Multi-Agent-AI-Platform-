"""Document Studio schemas (cp-0025). camelCase on the wire.

The documentation agent (Gemma) writes structured content from a prompt; it is
rendered to a real downloadable file in a chosen format (PPTX / DOCX / PDF), gated
by human approval. Offline / without the optional render libs it degrades to a
markdown deliverable (stub).
"""
from __future__ import annotations

from typing import Literal

from app.schemas.dashboard import CamelModel

DocFormat = Literal["pptx", "docx", "pdf"]
# Named visual themes the renderer styles with. "auto" lets the documentation agent
# pick one; anything else (or an unknown value) resolves to the default palette.
DocTheme = Literal["auto", "indigo", "emerald", "amber", "violet", "slate"]


class DocTable(CamelModel):
    """A simple tabular block: a header row + data rows (rendered as a styled table)."""

    headers: list[str] = []
    rows: list[list[str]] = []


class DocSection(CamelModel):
    """One section of a document. Beyond prose ``body`` it may carry a ``bullets`` list
    and/or a ``table`` so the renderer can lay out lists and tabular data (not just text)."""

    heading: str
    body: str = ""
    bullets: list[str] = []
    table: DocTable | None = None


class DocumentDraft(CamelModel):
    """A drafted document awaiting approval, then finalized for download."""

    id: str
    project_id: str
    prompt: str
    format: DocFormat
    title: str
    subtitle: str = ""  # cover subtitle / tagline (rendered on the title slide/page)
    theme: str = "indigo"  # resolved visual theme name (drives colors/banners/table styling)
    status: str = "awaiting_approval"  # awaiting_approval | approved | rejected
    sections: list[DocSection] = []
    artifacts: list[str] = []  # workspace-relative paths (the rendered file + content.json)
    file_path: str | None = None  # workspace-relative .pptx/.docx/.pdf (None in stub mode)
    stub: bool = False  # True when the render engine is absent (markdown deliverable)
    render_note: str | None = None  # render-engine / stub explanation (set at draft time; a decision never overwrites it)
    note: str | None = None  # human decision reason (set on reject) — kept separate from render_note (mirrors SocialDraft)
    created_at: str


class DocumentRequest(CamelModel):
    prompt: str
    format: DocFormat = "pdf"
    theme: DocTheme = "auto"  # "auto" -> the agent chooses; otherwise force this palette


class DocumentDecision(CamelModel):
    action: Literal["approve", "reject"]
    note: str | None = None
