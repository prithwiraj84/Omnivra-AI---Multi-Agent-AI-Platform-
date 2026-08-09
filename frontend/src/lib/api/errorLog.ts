/**
 * Error Log API (cp-0071). The backend captures every WARNING+ from its logging funnel —
 * provider failures, rate limits, TTS misses, render errors, unhandled crashes — classifies
 * and coalesces them, and serves them here scoped to the signed-in user.
 */
import { api } from '@/lib/api/client'

/** One captured error/warning (already coalesced server-side: `count` is the ×N). */
export interface ErrorItem {
  id: number
  /** First occurrence (ISO). */
  ts: string
  /** Most recent occurrence — what "how long ago" should show for a repeating error. */
  lastTs: string
  level: 'error' | 'warning'
  category: string
  /** module:function:line that produced it. */
  source: string
  message: string
  /** Exception type/value when one was attached, else ''. */
  detail: string
  count: number
}

export interface ErrorLogResponse {
  items: ErrorItem[]
  counts: Record<string, number>
  total: number
}

/** Newest-first error records + per-category counts. GET /system/errors. */
export async function getErrorLog(limit = 200): Promise<ErrorLogResponse> {
  const { data } = await api.get<ErrorLogResponse>('/system/errors', { params: { limit } })
  return data
}

/** Clear the current user's records. DELETE /system/errors. */
export async function clearErrorLog(): Promise<number> {
  const { data } = await api.delete<{ cleared: number }>('/system/errors')
  return data.cleared
}
