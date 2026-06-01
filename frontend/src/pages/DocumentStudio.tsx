import { useState, type FormEvent } from 'react'
import {
  Check,
  Download,
  FileText,
  FileType2,
  Loader2,
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
import type { DocFormat, DocumentDraft } from '@/lib/api/types'

const FORMATS: { value: DocFormat; label: string; icon: typeof FileText }[] = [
  { value: 'pptx', label: 'Presentation', icon: Presentation },
  { value: 'docx', label: 'Word doc', icon: FileText },
  { value: 'pdf', label: 'PDF', icon: FileType2 },
]
const FORMAT_LABEL: Record<string, string> = { pptx: 'PPTX', docx: 'DOCX', pdf: 'PDF' }

const STATUS_TONE: Record<string, BadgeTone> = {
  awaiting_approval: 'warning',
  approved: 'success',
  rejected: 'danger',
}
const STATUS_LABEL: Record<string, string> = {
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
        <Chip label={FORMAT_LABEL[draft.format] ?? draft.format.toUpperCase()} accent="blue" />
      </div>

      <div>
        <p className="text-sm font-semibold leading-snug text-[#fafafa]">{draft.title}</p>
        <p className="mt-0.5 truncate text-[11px] text-[#71717a]" title={draft.prompt}>
          {draft.prompt}
        </p>
      </div>

      {/* Content preview — section headings + first lines of body */}
      {draft.sections.length > 0 && (
        <div className="flex flex-col gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          {draft.sections.map((s, i) => (
            <div key={`${s.heading}|${i}`} className="text-xs">
              <p className="font-medium text-omnivra-cyan">{s.heading}</p>
              {s.body && <p className="mt-0.5 line-clamp-2 text-[#a1a1aa]">{s.body}</p>}
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
    generate.mutate({ prompt: p, format }, { onSuccess: () => setPrompt('') })
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
