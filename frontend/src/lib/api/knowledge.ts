/**
 * Knowledge base + Memory API calls (Phase 9). Uses the shared `@/lib/api/client`
 * axios instance (baseURL '/api'). The knowledge store is the long-lived RAG corpus
 * (workspace docs + manually-added notes); memory is the per-run agent recall store
 * the orchestrator writes after every run.
 */
import { api } from '@/lib/api/client'
import type { IngestResult, MemoryEntry, SearchHit, StoreStats } from '@/lib/api/types'

// --- Knowledge -------------------------------------------------------------

/** Semantic search over the knowledge base. GET /knowledge/search?q=&k=. */
export async function searchKnowledge(q: string, k = 8): Promise<SearchHit[]> {
  const { data } = await api.get<SearchHit[]>('/knowledge/search', { params: { q, k } })
  return data
}

/** Add a free-text note to the knowledge base. POST /knowledge. Returns the new id. */
export async function addKnowledge(text: string, source?: string): Promise<{ id: string }> {
  const { data } = await api.post<{ id: string }>('/knowledge', { text, source })
  return data
}

/** Ingest every workspace artifact into the knowledge base. POST /knowledge/ingest-workspace. */
export async function ingestWorkspace(): Promise<IngestResult> {
  const { data } = await api.post<IngestResult>('/knowledge/ingest-workspace')
  return data
}

/** Knowledge-base document count. GET /knowledge/stats. */
export async function knowledgeStats(): Promise<StoreStats> {
  const { data } = await api.get<StoreStats>('/knowledge/stats')
  return data
}

// --- Memory ----------------------------------------------------------------

/** Semantic search over the agent memory store. GET /memory/search?q=&k=. */
export async function searchMemory(q: string, k = 8): Promise<SearchHit[]> {
  const { data } = await api.get<SearchHit[]>('/memory/search', { params: { q, k } })
  return data
}

/** The most recent memory items (newest first). GET /memory/recent?n=. */
export async function recentMemory(n = 12): Promise<MemoryEntry[]> {
  const { data } = await api.get<MemoryEntry[]>('/memory/recent', { params: { n } })
  return data
}

/** Memory store item count. GET /memory/stats. */
export async function memoryStats(): Promise<StoreStats> {
  const { data } = await api.get<StoreStats>('/memory/stats')
  return data
}
