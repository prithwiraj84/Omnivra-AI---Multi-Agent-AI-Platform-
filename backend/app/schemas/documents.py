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
DocTheme = Literal[
    "auto", "indigo", "emerald", "amber", "violet", "slate",
    "crimson", "teal", "ocean", "sunset", "forest", "midnight", "rose",
]
ChartType = Literal["column", "bar", "line", "pie", "area"]
# Writing tone/style — now selects the document's GENRE: both HOW it's written (wording, sentence
# length, which blocks fit) AND its visual STRUCTURE (cover, columns, numbering, page frame,
# headings, dividers, callouts). Independent of `theme` (colors) and `font` (typeface).
DocStyle = Literal[
    "casual", "professional", "academic", "formal", "informal", "conversational", "technical",
    "business", "creative", "simple", "complex", "concise", "detailed", "persuasive", "informative",
    "neutral", "friendly", "seo-friendly", "marketing", "legal",
]
# Typeface family — chosen by the USER, independent of the genre/theme. Maps per format to concrete
# fonts (serif: Georgia/Times, sans: Calibri/Helvetica, mono: Consolas/Courier).
DocFont = Literal["serif", "sans", "mono"]


class DocTable(CamelModel):
    """A simple tabular block: a header row + data rows (rendered as a styled table)."""

    headers: list[str] = []
    rows: list[list[str]] = []


class DocSeries(CamelModel):
    """One data series of a chart: a name + numeric values aligned to the chart's categories."""

    name: str = ""
    values: list[float] = []


class DocChart(CamelModel):
    """A chart/graph spec the renderer draws natively in PPTX (and as a data table in DOCX/PDF)."""

    type: ChartType = "column"
    title: str = ""
    categories: list[str] = []
    series: list[DocSeries] = []


class DocImage(CamelModel):
    """A generated illustration for a section. ``prompt`` is what the image depicts; ``path`` is the
    workspace-relative path to the rendered image once generated (None = requested but not produced,
    e.g. no HF key / generation failed — the document still renders without it)."""

    prompt: str = ""
    alt: str = ""
    path: str | None = None


class DocSection(CamelModel):
    """One section of a document. Beyond prose ``body`` it may carry a ``bullets`` list, a
    ``table`` for tabular data, a ``chart`` for data shown as a graph, and/or an ``image``
    (FLUX-generated illustration, gated by the genre's image policy)."""

    heading: str
    body: str = ""
    bullets: list[str] = []
    table: DocTable | None = None
    chart: DocChart | None = None
    image: DocImage | None = None


class DocumentDraft(CamelModel):
    """A drafted document awaiting approval, then finalized for download."""

    id: str
    project_id: str
    prompt: str
    format: DocFormat
    title: str
    subtitle: str = ""  # cover subtitle / tagline (rendered on the title slide/page)
    theme: str = "indigo"  # resolved visual theme name (drives colors/banners/table styling)
    style: str = "professional"  # genre — drives prose AND visual structure
    font: str = "sans"  # typeface family (serif | sans | mono), user-chosen
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
    style: DocStyle = "professional"  # genre (casual / academic / legal / marketing / …)
    font: DocFont = "sans"  # typeface family — user-chosen, independent of genre/theme


class DocumentDecision(CamelModel):
    action: Literal["approve", "reject"]
    note: str | None = None
