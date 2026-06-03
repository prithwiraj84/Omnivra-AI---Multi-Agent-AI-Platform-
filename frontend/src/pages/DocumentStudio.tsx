import { useState, type FormEvent } from 'react'
import {
  Check,
  Download,
  FileText,
  FileType2,
  Loader2,
  Palette,
  Presentation,
  Wand2,
  X,
} from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { Chip } from '@/components/ui/chip'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import { cn } from '@/lib/utils'
import { useDecideDocument, useDocuments, useGenerateDocument } from '@/hooks/useDocuments'
import { documentUrl } from '@/lib/api/documents'
import { useProjectStore } from '@/store/project'
import type { DocFormat, DocTable, DocTheme, DocumentDraft } from '@/lib/api/types'

const FORMATS: { value: DocFormat; label: string; icon: typeof FileText }[] = [
  { value: 'pptx', label: 'Presentation', icon: Presentation },
  { value: 'docx', label: 'Word doc', icon: FileText },
  { value: 'pdf', label: 'PDF', icon: FileType2 },
]
const FORMAT_LABEL: Record<string, string> = { pptx: 'PPTX', docx: 'DOCX', pdf: 'PDF' }

/** Visual theme palettes — mirrors backend doc_render.THEMES. 'auto' lets the agent pick. */
const THEMES: { value: DocTheme; label: string; swatch: string }[] = [
  { value: 'auto', label: 'Auto', swatch: 'linear-gradient(135deg, #06b6d4, #7c3aed)' },
  { value: 'indigo', label: 'Indigo', swatch: '#4F46E5' },
  { value: 'emerald', label: 'Emerald', swatch: '#059669' },
  { value: 'amber', label: 'Amber', swatch: '#D97706' },
  { value: 'violet', label: 'Violet', swatch: '#7C3AED' },
  { value: 'slate', label: 'Slate', swatch: '#334155' },
]
/** Resolved (non-auto) palette colors, for the per-card theme dot. */
const THEME_HEX: Record<string, string> = {
  indigo: '#4F46E5',
  emerald: '#059669',
  amber: '#D97706',
  violet: '#7C3AED',
  slate: '#334155',
}

/** Compact in-card preview of a section's table (header + first rows). */
function MiniTable({ table }: { table: DocTable }) {
  const headers = table.headers.length ? table.headers : table.rows[0]?.map(() => '') ?? []
  const rows = table.rows.slice(0, 3)
  if (!headers.length && !rows.length) return null
  return (
    <div className="mt-1.5 overflow-hidden rounded border border-white/[0.08]">
      <table className="w-full border-collapse text-[10px]">
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} className="border-b border-white/[0.08] bg-white/[0.05] px-1.5 py-1 text-left font-semibold text-[#d4d4d8]">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={ri}>
              {r.map((c, ci) => (
                <td key={ci} className="border-b border-white/[0.04] px-1.5 py-1 text-[#a1a1aa]">
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {table.rows.length > 3 && (
        <p className="px-1.5 py-0.5 text-[10px] text-[#71717a]">+{table.rows.length - 3} more rows</p>
      )}
    </div>
  )
}

const STATUS_TONE: Record<string, BadgeTone> = {
  generating: 'info',
  awaiting_approval: 'warning',
  approved: 'success',
  rejected: 'danger',
}
const STATUS_LABEL: Record<string, string> = {
  generating: 'Generating…',
  awaiting_approval: 'Awaiting approval',
  approved: 'Approved',
  rejected: 'Rejected',
}

/** One drafted document with its content preview, download, and approve/reject controls. */
function DocumentCard({
  draft,
  projectId,
  onDecide,
  busy,
}: {
  draft: DocumentDraft
  projectId: string
  onDecide: (id: string, action: 'approve' | 'reject') => void
  busy: boolean
}) {
  return (
    <GlassCard className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <NeonBadge tone="cyan">
            <FileText className="h-3 w-3" aria-hidden />
            document
          </NeonBadge>
          <NeonBadge tone={STATUS_TONE[draft.status] ?? 'info'} dot>
            {STATUS_LABEL[draft.status] ?? draft.status}
          </NeonBadge>
        </div>
        <div className="flex items-center gap-2">
          {/* The 'generating' placeholder theme is provisional (the agent may pick another), so
              only show the palette dot once the draft is terminal. */}
          {draft.status !== 'generating' && draft.theme && THEME_HEX[draft.theme] && (
            <span
              className="h-3 w-3 rounded-full ring-1 ring-white/20"
              style={{ background: THEME_HEX[draft.theme] }}
              title={`${draft.theme} theme`}
              aria-label={`${draft.theme} theme`}
            />
          )}
          <Chip label={FORMAT_LABEL[draft.format] ?? draft.format.toUpperCase()} accent="blue" />
        </div>
      </div>

      <div>
        <p className="text-sm font-semibold leading-snug text-[#fafafa]">{draft.title}</p>
        <p className="mt-0.5 truncate text-[11px] text-[#71717a]" title={draft.prompt}>
          {draft.prompt}
        </p>
      </div>

      {/* Generating — fire-and-poll progress bar (content + render happen in the background). */}
      {draft.status === 'generating' && (
        <div className="flex flex-col gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          <div className="flex items-center gap-2 text-xs text-[#a1a1aa]" role="status" aria-live="polite">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-omnivra-cyan" aria-hidden />
            Writing the content & rendering your {FORMAT_LABEL[draft.format] ?? draft.format.toUpperCase()}…
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]" role="progressbar" aria-label="Generating document">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-omnivra-cyan" />
          </div>
        </div>
      )}

      {/* Content preview — section headings, body, bullets + a mini table */}
      {draft.sections.length > 0 && (
        <div className="flex flex-col gap-2.5 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          {draft.sections.map((s, i) => (
            <div key={`${s.heading}|${i}`} className="text-xs">
              <p className="font-medium text-omnivra-cyan">{s.heading}</p>
              {s.body && <p className="mt-0.5 line-clamp-2 text-[#a1a1aa]">{s.body}</p>}
              {s.bullets && s.bullets.length > 0 && (
                <ul className="mt-1 space-y-0.5">
                  {s.bullets.slice(0, 4).map((b, bi) => (
                    <li key={bi} className="flex gap-1.5 text-[#a1a1aa]">
                      <span className="text-omnivra-cyan" aria-hidden>
                        •
                      </span>
                      <span className="line-clamp-1">{b}</span>
                    </li>
                  ))}
                  {s.bullets.length > 4 && (
                    <li className="text-[10px] text-[#71717a]">+{s.bullets.length - 4} more</li>
                  )}
                </ul>
              )}
              {s.table && <MiniTable table={s.table} />}
            </div>
          ))}
        </div>
      )}

      {/* Stub notice — render engine absent, markdown deliverable instead. Driven by
          `stub` (+ the dedicated renderNote), never the mutable decision `note`, so it
          survives approval/rejection. */}
      {draft.stub && (
        <p className="rounded-md border border-omnivra-amber/20 bg-omnivra-amber/[0.05] px-2.5 py-1.5 text-[11px] text-omnivra-amber">
          {draft.renderNote ?? 'Render engine not installed — a Markdown deliverable was saved instead.'}
        </p>
      )}

      {/* Download the rendered file (or markdown deliverable) */}
      {draft.filePath && (
        <a
          href={documentUrl(draft.filePath, projectId)}
          download
          className="focus-ring inline-flex items-center gap-1.5 self-start rounded-md border border-white/10 px-2.5 py-1.5 text-xs font-medium text-[#d4d4d8] transition-colors duration-200 hover:border-omnivra-cyan/40 hover:text-omnivra-cyan"
        >
          <Download className="h-3.5 w-3.5" aria-hidden />
          Download {draft.stub ? 'Markdown' : (FORMAT_LABEL[draft.format] ?? draft.format.toUpperCase())}
        </a>
      )}

      {draft.status === 'rejected' && draft.note && (
        <p className="text-[11px] text-omnivra-pink">Rejected: {draft.note}</p>
      )}

      {/* Approve / reject — only while awaiting approval */}
      {draft.status === 'awaiting_approval' && (
        <div className="flex items-center gap-2 pt-0.5">
          <Button type="button" size="sm" disabled={busy} onClick={() => onDecide(draft.id, 'approve')} className="flex-1">
            {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Check className="h-3.5 w-3.5" aria-hidden />}
            Approve
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => onDecide(draft.id, 'reject')}
            className="flex-1 hover:text-omnivra-red"
          >
            <X className="h-3.5 w-3.5" aria-hidden />
            Reject
          </Button>
        </div>
      )}
    </GlassCard>
  )
}

/**
 * Document Studio — generate a custom document (presentation / Word doc / PDF) from a
 * prompt. The documentation agent (Gemma) writes structured content; it is rendered to
 * the chosen format and gated on human approval before it's a finished deliverable.
 * Offline / without the optional render engine each draft degrades to a downloadable
 * markdown deliverable (stub). Scoped to the active project.
 */
export function DocumentStudio() {
  const [prompt, setPrompt] = useState('')
  const [format, setFormat] = useState<DocFormat>('pdf')
  const [theme, setTheme] = useState<DocTheme>('auto')

  const { data: documents } = useDocuments()
  const generate = useGenerateDocument()
  const decide = useDecideDocument()
  const activeProjectId = useProjectStore((s) => s.activeProjectId)

  const list = documents ?? []
  const generating = generate.isPending

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const p = prompt.trim()
    if (!p || generating) return
    generate.mutate({ prompt: p, format, theme }, { onSuccess: () => setPrompt('') })
  }

  const onDecide = (id: string, action: 'approve' | 'reject') => decide.mutate({ id, decision: { action } })
  const busyId = decide.isPending ? decide.variables?.id : undefined

  return (
    <div className="flex flex-col gap-5">
      <GlassCard padding="none" className="overflow-hidden">
        <div className="flex flex-col gap-4 p-5">
          <SectionHeader label="Document Studio" count={list.length} />

          <form onSubmit={submit} className="flex flex-col gap-3">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the document. e.g. ‘A 5-slide investor pitch for our AI company OS’"
              aria-label="Document prompt"
              rows={2}
              className="focus-ring min-h-[3.5rem] w-full resize-y rounded-md bg-omnivra-surface-2 px-3 py-2 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
            />

            <div className="flex flex-wrap items-center gap-3">
              {/* Format picker */}
              <div className="inline-flex rounded-md bg-omnivra-surface-2 p-0.5" role="group" aria-label="Document format">
                {FORMATS.map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    type="button"
                    aria-pressed={format === value}
                    onClick={() => setFormat(value)}
                    className={cn(
                      'focus-ring inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium transition-colors duration-200',
                      format === value ? 'bg-omnivra-surface-3 text-omnivra-cyan' : 'text-[#a1a1aa] hover:text-[#e4e4e7]',
                    )}
                  >
                    <Icon className="h-3.5 w-3.5" aria-hidden />
                    {label}
                  </button>
                ))}
              </div>

              {/* Style picker — colored swatches drive the rendered document's palette */}
              <div className="inline-flex items-center gap-1.5" role="group" aria-label="Document style">
                <Palette className="h-3.5 w-3.5 text-[#71717a]" aria-hidden />
                {THEMES.map(({ value, label, swatch }) => (
                  <button
                    key={value}
                    type="button"
                    title={label}
                    aria-label={`Style: ${label}`}
                    aria-pressed={theme === value}
                    onClick={() => setTheme(value)}
                    className={cn(
                      'focus-ring grid h-6 w-6 place-items-center rounded-full border transition-all duration-200',
                      theme === value ? 'border-white ring-2 ring-omnivra-cyan/50' : 'border-white/15 hover:border-white/40',
                    )}
                    style={{ background: swatch }}
                  >
                    {value === 'auto' && <span className="text-[8px] font-bold text-white">A</span>}
                  </button>
                ))}
              </div>

              <Button type="submit" size="sm" disabled={generating || prompt.trim().length === 0} className="ml-auto">
                {generating ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Wand2 className="h-4 w-4" aria-hidden />}
                {generating ? 'Drafting…' : 'Generate document'}
              </Button>
            </div>

            {generate.isError && (
              <p className="text-xs text-omnivra-pink" role="status" aria-live="polite">
                Could not generate the document. Is the backend running?
              </p>
            )}
          </form>
        </div>
      </GlassCard>

      {list.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          hint="Describe a document above, pick a format, and hit Generate. Drafts wait here for your approval."
          className="py-16"
        />
      ) : (
        <Stagger className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
          {list.map((draft) => (
            <StaggerItem key={draft.id}>
              <DocumentCard draft={draft} projectId={activeProjectId} onDecide={onDecide} busy={busyId === draft.id} />
            </StaggerItem>
          ))}
        </Stagger>
      )}
    </div>
  )
}
