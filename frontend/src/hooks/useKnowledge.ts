/**
 * Knowledge base hooks (Phase 9).
 *  - useKnowledgeSearch(query): semantic search, only fired once the query has more
 *    than one character (enabled: query.length > 1) so we don't spam single-key terms.
 *  - useKnowledgeStats(): the live document count for the SectionHeader badge.
 *  - useIngestWorkspace(): a mutation that ingests every workspace artifact, then
 *    invalidates the knowledge queries so the count + any active search refresh.
 * All fail gracefully offline (jsdom/tests) — consumers default to [] / undefined
 * and render the empty state rather than crashing.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ingestWorkspace, knowledgeStats, searchKnowledge } from '@/lib/api/knowledge'
import type { IngestResult, SearchHit, StoreStats } from '@/lib/api/types'

/** Knowledge search; disabled until the query is at least two characters long. */
export function useKnowledgeSearch(query: string) {
  return useQuery<SearchHit[]>({
    queryKey: ['knowledge', 'search', query],
    queryFn: () => searchKnowledge(query),
    enabled: query.length > 1,
    retry: 1,
  })
}

/** Knowledge-base document count — one retry so an offline host settles quickly. */
export function useKnowledgeStats() {
  return useQuery<StoreStats>({
    queryKey: ['knowledge', 'stats'],
    queryFn: knowledgeStats,
    retry: 1,
  })
}

/** Ingest the workspace into the knowledge base; refreshes the count + search on success. */
export function useIngestWorkspace() {
  const qc = useQueryClient()
  return useMutation<IngestResult, Error, void>({
    mutationFn: () => ingestWorkspace(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['knowledge'] })
    },
  })
}
