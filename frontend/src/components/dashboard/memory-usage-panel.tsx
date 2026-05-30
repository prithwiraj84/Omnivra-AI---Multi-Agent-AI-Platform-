import { Brain, Database, Sparkles } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { IconTile } from '@/components/ui/icon-tile'
import { EmptyState } from '@/components/ui/empty-state'
import { useMemoryStats, useRecentMemory } from '@/hooks/useMemory'
import { useKnowledgeStats } from '@/hooks/useKnowledge'
import type { Accent } from '@/types'
import type { LucideIcon } from 'lucide-react'

/** Format a count with thousands separators, falling back to a placeholder dash. */
function formatCount(count: number | undefined): string {
  if (count === undefined) return '—'
  return count.toLocaleString('en-US')
}

/** One store tile: tinted IconTile + big count + label. */
function StoreTile({
  icon,
  accent,
  count,
  label,
}: {
  icon: LucideIcon
  accent: Accent
  count: number | undefined
  label: string
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3.5">
      <IconTile accent={accent} icon={icon} />
      <div className="min-w-0">
        <p className="tabular text-2xl font-semibold leading-tight text-[#e4e4e7]">
          {formatCount(count)}
        </p>
        <p className="truncate text-xs text-[#71717a]">{label}</p>
      </div>
    </div>
  )
}

/**
 * MemoryUsagePanel — the Memory usage detail panel (DESIGN_SYSTEM 8.3). Shows the
 * two vector-store sizes side by side (useMemoryStats + useKnowledgeStats) as
 * IconTile + big count tiles, plus a small "recent memory" preview of the newest
 * five snippets (useRecentMemory(5)). Offline (jsdom/tests) the queries never
 * resolve, counts render a dash and the preview shows the EmptyState — never crashes.
 */
export function MemoryUsagePanel() {
  const { data: memory } = useMemoryStats()
  const { data: knowledge } = useKnowledgeStats()
  const { data: recent } = useRecentMemory(5)

  const recentItems = recent ?? []

  return (
    <GlassCard padding="md" glow="violet" className="flex flex-col gap-4">
      <SectionHeader label="Memory & Knowledge" />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <StoreTile icon={Brain} accent="violet" count={memory?.count} label="Memory items" />
        <StoreTile
          icon={Database}
          accent="cyan"
          count={knowledge?.count}
          label="Knowledge documents"
        />
      </div>

      <div className="flex flex-col gap-2">
        <span className="section-label">Recent Memory</span>
        {recentItems.length === 0 ? (
          <EmptyState
            icon={Sparkles}
            title="No memories yet"
            hint="Run a workflow — each agent's output is stored here as recall."
            className="py-8"
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {recentItems.map((item) => (
              <li
                key={item.id}
                className="flex items-start gap-2.5 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3"
              >
                <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-omnivra-purple" aria-hidden />
                <p className="line-clamp-2 text-xs leading-relaxed text-[#a1a1aa]">{item.text}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </GlassCard>
  )
}
