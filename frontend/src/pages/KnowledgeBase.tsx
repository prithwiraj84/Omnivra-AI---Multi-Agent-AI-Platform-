import { useState } from 'react'
import { BookOpen, Database, FileSearch, Layers, Search } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { ScrollArea } from '@/components/ui/scroll-area'
import { NeonBadge } from '@/components/ui/neon-badge'
import { EmptyState } from '@/components/ui/empty-state'
import { Button } from '@/components/ui/button'
import { useIngestWorkspace, useKnowledgeSearch, useKnowledgeStats } from '@/hooks/useKnowledge'
import type { SearchHit } from '@/lib/api/types'

/** Read a string field from a metadata bag, falling back to `undefined`. */
function metaString(metadata: Record<string, unknown>, key: string): string | undefined {
  const value = metadata[key]
  return typeof value === 'string' && value.length > 0 ? value : undefined
}

/** Render a cosine score (0..1) as a compact percentage chip. */
function scorePct(score: number): string {
  return `${Math.round(score * 100)}%`
}

/** One knowledge-base search result row: snippet + source + relevance score. */
function HitRow({ hit }: { hit: SearchHit }) {
  const source = metaString(hit.metadata, 'source') ?? metaString(hit.metadata, 'path')
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3.5">
      <div className="flex items-start justify-between gap-3">
        <p className="min-w-0 flex-1 text-sm leading-relaxed text-[#e4e4e7]">{hit.text}</p>
        <NeonBadge tone="cyan" className="tabular shrink-0">
          {scorePct(hit.score)}
        </NeonBadge>
      </div>
      {source && (
        <div className="flex items-center gap-1.5 text-xs text-[#71717a]">
          <FileSearch className="h-3.5 w-3.5 shrink-0" aria-hidden />
          <span className="truncate font-mono">{source}</span>
        </div>
      )}
    </div>
  )
}

/**
 * KnowledgeBase — the RAG corpus browser. A glass panel with a "Knowledge Base"
 * SectionHeader (+ a live document-count badge) and an "Ingest Workspace" action.
 * A search field runs semantic search (enabled past one character) and lists
 * SearchHit rows — each showing the snippet, a relevance NeonBadge and the source
 * from metadata. Shows an EmptyState when there's no query or no results. Offline
 * (jsdom/tests) the queries simply never resolve and the empty state renders.
 */
export function KnowledgeBase() {
  const [query, setQuery] = useState('')
  const trimmed = query.trim()

  const { data: stats } = useKnowledgeStats()
  const { data: hits, isFetching } = useKnowledgeSearch(trimmed)
  const ingest = useIngestWorkspace()

  const hasQuery = trimmed.length > 1
  const results = hits ?? []

  return (
    <GlassCard padding="none" className="overflow-hidden">
      <div className="flex flex-col gap-4 border-b border-white/5 p-5">
        <SectionHeader
          label="Knowledge Base"
          count={stats?.count}
          action={
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => ingest.mutate()}
              disabled={ingest.isPending}
            >
              <Layers aria-hidden />
              {ingest.isPending ? 'Ingesting…' : 'Ingest Workspace'}
            </Button>
          }
        />

        <div className="relative flex items-center">
          <Search
            className="pointer-events-none absolute left-3 h-[18px] w-[18px] text-[#71717a]"
            aria-hidden
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search the knowledge base…"
            aria-label="Search the knowledge base"
            className="focus-ring h-9 w-full rounded-md bg-omnivra-surface-2 pl-10 pr-3 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
          />
        </div>

        {ingest.isSuccess && ingest.data && (
          <p className="text-xs text-omnivra-emerald" role="status" aria-live="polite">
            Ingested {ingest.data.ingested} artifact{ingest.data.ingested === 1 ? '' : 's'} ·{' '}
            <span className="text-[#71717a]">{ingest.data.total} documents total</span>
          </p>
        )}
        {ingest.isError && (
          <p className="text-xs text-omnivra-pink" role="status" aria-live="polite">
            Could not ingest the workspace. Try again.
          </p>
        )}
      </div>

      {!hasQuery ? (
        <EmptyState
          icon={BookOpen}
          title="Search your knowledge"
          hint="Type a query to retrieve the most relevant notes and ingested workspace docs."
          className="py-16"
        />
      ) : results.length === 0 ? (
        <EmptyState
          icon={Database}
          title={isFetching ? 'Searching…' : 'No matches found'}
          hint={
            isFetching
              ? 'Looking through the corpus for relevant passages.'
              : 'Nothing in the knowledge base matched. Try ingesting the workspace or a broader query.'
          }
          className="py-16"
        />
      ) : (
        <ScrollArea className="max-h-[32rem]">
          <div className="flex flex-col gap-2 p-4">
            {results.map((hit) => (
              <HitRow key={hit.id} hit={hit} />
            ))}
          </div>
        </ScrollArea>
      )}
    </GlassCard>
  )
}
