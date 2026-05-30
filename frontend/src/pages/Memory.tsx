import { useState } from 'react'
import { Brain, History, Search, Sparkles } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { ScrollArea } from '@/components/ui/scroll-area'
import { NeonBadge } from '@/components/ui/neon-badge'
import { EmptyState } from '@/components/ui/empty-state'
import { MemoryUsagePanel } from '@/components/dashboard/memory-usage-panel'
import { useMemorySearch, useMemoryStats, useRecentMemory } from '@/hooks/useMemory'

/** Read a string field from a metadata bag, falling back to `undefined`. */
function metaString(metadata: Record<string, unknown>, key: string): string | undefined {
  const value = metadata[key]
  return typeof value === 'string' && value.length > 0 ? value : undefined
}

/** Resolve the originating agent from a memory item's metadata. */
function agentOf(metadata: Record<string, unknown>): string | undefined {
  return metaString(metadata, 'agentId') ?? metaString(metadata, 'agent')
}

/** Render a cosine score (0..1) as a compact percentage. */
function scorePct(score: number): string {
  return `${Math.round(score * 100)}%`
}

/** One memory row: text snippet + the agent that produced it, plus an optional score. */
function MemoryRow({
  text,
  metadata,
  score,
}: {
  text: string
  metadata: Record<string, unknown>
  score?: number
}) {
  const agent = agentOf(metadata)
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3.5">
      <div className="flex items-start justify-between gap-3">
        <p className="min-w-0 flex-1 text-sm leading-relaxed text-[#e4e4e7]">{text}</p>
        {score !== undefined && (
          <NeonBadge tone="violet" className="tabular shrink-0">
            {scorePct(score)}
          </NeonBadge>
        )}
      </div>
      {agent && (
        <div className="flex items-center gap-1.5 text-xs text-[#71717a]">
          <Sparkles className="h-3.5 w-3.5 shrink-0" aria-hidden />
          <span className="truncate">{agent}</span>
        </div>
      )}
    </div>
  )
}

/**
 * Memory — the agent recall store. A glass panel with a "Memory" SectionHeader
 * (+ a live item-count badge). A search field runs semantic recall (enabled past
 * one character) and, when there's no active query, falls back to a "Recent" list
 * of the newest memory items. Each row shows the memory text snippet and the agent
 * that produced it (from metadata). Offline (jsdom/tests) the queries never resolve
 * and the EmptyState renders without crashing.
 */
export function Memory() {
  const [query, setQuery] = useState('')
  const trimmed = query.trim()
  const hasQuery = trimmed.length > 1

  const { data: stats } = useMemoryStats()
  const { data: recent } = useRecentMemory(12)
  const { data: hits, isFetching } = useMemorySearch(trimmed)

  const recentItems = recent ?? []
  const searchResults = hits ?? []

  return (
    <div className="flex flex-col gap-5">
      <MemoryUsagePanel />

      <GlassCard padding="none" className="overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-white/5 p-5">
          <SectionHeader label="Memory" count={stats?.count} />

        <div className="relative flex items-center">
          <Search
            className="pointer-events-none absolute left-3 h-[18px] w-[18px] text-[#71717a]"
            aria-hidden
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Recall a memory…"
            aria-label="Search agent memory"
            className="focus-ring h-9 w-full rounded-md bg-omnivra-surface-2 pl-10 pr-3 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
          />
        </div>
      </div>

      {hasQuery ? (
        searchResults.length === 0 ? (
          <EmptyState
            icon={Brain}
            title={isFetching ? 'Recalling…' : 'No memories matched'}
            hint={
              isFetching
                ? 'Searching the recall store for relevant context.'
                : 'Nothing in memory matched that query. Try a broader phrasing.'
            }
            className="py-16"
          />
        ) : (
          <ScrollArea className="max-h-[32rem]">
            <div className="flex flex-col gap-2 p-4">
              {searchResults.map((hit) => (
                <MemoryRow key={hit.id} text={hit.text} metadata={hit.metadata} score={hit.score} />
              ))}
            </div>
          </ScrollArea>
        )
      ) : recentItems.length === 0 ? (
        <EmptyState
          icon={History}
          title="No memories yet"
          hint="Run a workflow — each agent's output is stored here as recall for future runs."
          className="py-16"
        />
      ) : (
        <>
          <div className="px-5 pt-4">
            <span className="section-label">Recent</span>
          </div>
          <ScrollArea className="max-h-[30rem]">
            <div className="flex flex-col gap-2 p-4">
              {recentItems.map((item) => (
                <MemoryRow key={item.id} text={item.text} metadata={item.metadata} />
              ))}
            </div>
          </ScrollArea>
        </>
      )}
      </GlassCard>
    </div>
  )
}
