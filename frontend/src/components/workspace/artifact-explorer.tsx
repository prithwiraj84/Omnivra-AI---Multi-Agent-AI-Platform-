import { useMemo, useState } from 'react'
import {
  Code2,
  FileCode,
  FileText,
  Folder,
  Presentation,
  ScrollText,
  type LucideIcon,
} from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { ScrollArea } from '@/components/ui/scroll-area'
import { IconTile } from '@/components/ui/icon-tile'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { EmptyState } from '@/components/ui/empty-state'
import { useArtifacts, useArtifact } from '@/hooks/useArtifacts'
import { cn } from '@/lib/utils'
import type { Accent } from '@/types'
import type { Artifact } from '@/lib/api/types'

export interface ArtifactExplorerProps {
  /** Restrict the list to one workspace category (e.g. "docs"). Omit for all. */
  category?: string
  /** SectionHeader title (e.g. "Workspace Artifacts"). */
  title: string
}

/** Per-category presentation: list icon, accent tint, badge tone. */
interface CategoryStyle {
  icon: LucideIcon
  accent: Accent
  tone: BadgeTone
}

const CATEGORY_STYLES: Record<string, CategoryStyle> = {
  frontend: { icon: Code2, accent: 'blue', tone: 'info' },
  backend: { icon: FileCode, accent: 'violet', tone: 'violet' },
  docs: { icon: FileText, accent: 'cyan', tone: 'cyan' },
  presentations: { icon: Presentation, accent: 'pink', tone: 'warning' },
  reports: { icon: ScrollText, accent: 'emerald', tone: 'success' },
}

const DEFAULT_STYLE: CategoryStyle = { icon: Folder, accent: 'cyan', tone: 'info' }

function styleFor(category: string): CategoryStyle {
  return CATEGORY_STYLES[category] ?? DEFAULT_STYLE
}

/** Format an ISO timestamp into a compact local "MMM d, HH:mm" — falls back to the raw string. */
function formatModified(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** One selectable row in the left pane. */
function ArtifactRow({
  artifact,
  selected,
  onSelect,
}: {
  artifact: Artifact
  selected: boolean
  onSelect: () => void
}) {
  const style = styleFor(artifact.category)
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-current={selected}
      className={cn(
        'flex w-full items-center gap-3 rounded-lg border border-transparent px-2.5 py-2 text-left transition-colors',
        'hover:bg-white/[0.04]',
        selected && 'border-white/10 bg-white/[0.06]',
      )}
    >
      <IconTile accent={style.accent} size="sm" icon={style.icon} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-[#e4e4e7]">{artifact.path}</p>
        <p className="truncate text-xs text-[#71717a]">
          {artifact.agentId ?? 'unknown agent'} · {formatModified(artifact.modified)}
        </p>
      </div>
      <NeonBadge tone={style.tone} className="shrink-0 capitalize">
        {artifact.category}
      </NeonBadge>
    </button>
  )
}

/**
 * ArtifactExplorer — two-pane workspace browser. LEFT: a scrollable list of
 * artifacts (filtered to `category` when given), each row showing a category
 * IconTile, the path + agent, a category NeonBadge and the modified time;
 * clicking selects it. RIGHT: the selected artifact's content in a scrollable
 * mono <pre> with its path as a header. Shows an EmptyState when the workspace
 * has no artifacts yet. Polls every 10s via useArtifacts.
 */
export function ArtifactExplorer({ category, title }: ArtifactExplorerProps) {
  const { data: artifacts } = useArtifacts()
  const [selectedPath, setSelectedPath] = useState<string | null>(null)

  const items = useMemo(() => {
    const all = artifacts ?? []
    return category ? all.filter((a) => a.category === category) : all
  }, [artifacts, category])

  const { data: content, isFetching } = useArtifact(selectedPath)

  return (
    <GlassCard padding="none" className="overflow-hidden">
      <div className="border-b border-white/5 p-5">
        <SectionHeader label={title} count={items.length} />
      </div>

      {items.length === 0 ? (
        <EmptyState
          icon={Folder}
          title="No artifacts yet"
          hint="Assign a task to the CEO — each agent's output lands here in the workspace."
          className="py-16"
        />
      ) : (
        <div className="grid min-h-[26rem] grid-cols-1 lg:grid-cols-[20rem_1fr]">
          {/* LEFT: artifact list */}
          <ScrollArea className="max-h-[34rem] border-b border-white/5 lg:border-b-0 lg:border-r">
            <div className="flex flex-col gap-1 p-3">
              {items.map((artifact) => (
                <ArtifactRow
                  key={artifact.path}
                  artifact={artifact}
                  selected={artifact.path === selectedPath}
                  onSelect={() => setSelectedPath(artifact.path)}
                />
              ))}
            </div>
          </ScrollArea>

          {/* RIGHT: selected content viewer */}
          <div className="flex min-w-0 flex-col">
            {selectedPath ? (
              <>
                <div className="flex items-center gap-2 border-b border-white/5 px-4 py-3">
                  <FileText className="h-4 w-4 shrink-0 text-omnivra-cyan" aria-hidden />
                  <span className="truncate font-mono text-xs text-[#a1a1aa]">{selectedPath}</span>
                </div>
                <ScrollArea className="max-h-[30rem] flex-1">
                  <pre className="whitespace-pre-wrap break-words p-4 font-mono text-xs leading-relaxed text-[#e4e4e7]">
                    {content?.content ?? (isFetching ? 'Loading…' : '')}
                  </pre>
                </ScrollArea>
              </>
            ) : (
              <EmptyState
                icon={FileText}
                title="Select an artifact"
                hint="Pick a file on the left to preview its contents."
                className="my-auto"
              />
            )}
          </div>
        </div>
      )}
    </GlassCard>
  )
}
