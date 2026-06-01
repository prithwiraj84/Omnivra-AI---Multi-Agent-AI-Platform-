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


class DocSection(CamelModel):
    heading: str
    body: str = ""


class DocumentDraft(CamelModel):
    """A drafted document awaiting approval, then finalized for download."""

    id: str
    project_id: str
    prompt: str
    format: DocFormat
    title: str
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


class DocumentDecision(CamelModel):
    action: Literal["approve", "reject"]
    note: str | None = None
