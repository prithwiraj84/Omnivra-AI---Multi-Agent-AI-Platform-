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

/** The most recent memory items (newest first). */
export function useRecentMemory(n = 12) {
  return useQuery<MemoryEntry[]>({
    queryKey: ['memory', 'recent', n],
    queryFn: () => recentMemory(n),
    retry: 1,
  })
}

/** Memory search; disabled until the query is at least two characters long. */
export function useMemorySearch(query: string) {
  return useQuery<SearchHit[]>({
    queryKey: ['memory', 'search', query],
    queryFn: () => searchMemory(query),
    enabled: query.length > 1,
    retry: 1,
  })
}

/** Memory store item count — one retry so an offline host settles quickly. */
export function useMemoryStats() {
  return useQuery<StoreStats>({
    queryKey: ['memory', 'stats'],
    queryFn: memoryStats,
    retry: 1,
  })
}
