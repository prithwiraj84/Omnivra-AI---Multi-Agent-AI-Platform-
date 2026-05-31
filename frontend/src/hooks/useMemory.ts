/**
 * Agent memory hooks (Phase 9).
 *  - useRecentMemory(n): the newest memory items the orchestrator wrote after each run.
 *  - useMemorySearch(query): semantic recall, only fired once the query has more than
 *    one character (enabled: query.length > 1).
 *  - useMemoryStats(): the live memory item count for the SectionHeader badge.
 * All fail gracefully offline (jsdom/tests) — consumers default to [] / undefined
 * and render the empty state rather than crashing.
 */
import { useQuery } from '@tanstack/react-query'
import { memoryStats, recentMemory, searchMemory } from '@/lib/api/knowledge'
import type { MemoryEntry, SearchHit, StoreStats } from '@/lib/api/types'
import { useProjectStore } from '@/store/project'

/** The most recent memory items (newest first), scoped to the active project. */
export function useRecentMemory(n = 12) {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<MemoryEntry[]>({
    queryKey: ['memory', 'recent', projectId, n],
    queryFn: () => recentMemory(n),
    retry: 1,
  })
}

/** Memory search; disabled until the query is at least two characters long (per project). */
export function useMemorySearch(query: string) {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<SearchHit[]>({
    queryKey: ['memory', 'search', projectId, query],
    queryFn: () => searchMemory(query),
    enabled: query.length > 1,
    retry: 1,
  })
}

/** Memory store item count for the active project. */
export function useMemoryStats() {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<StoreStats>({
    queryKey: ['memory', 'stats', projectId],
    queryFn: memoryStats,
    retry: 1,
  })
}
