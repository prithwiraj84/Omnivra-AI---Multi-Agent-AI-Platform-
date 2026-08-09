/**
 * Error Log hooks (cp-0071).
 *  - useErrorLog(): the captured error records, polled + refreshed live by the 'error_log'
 *    WebSocket frame (useWebSocket invalidates the query).
 *  - useClearErrorLog(): wipe the log.
 *  - useErrorBadge(): how many records arrived since the user last OPENED the page — drives
 *    the sidebar badge, so it clears on visit rather than nagging forever.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { clearErrorLog, getErrorLog, type ErrorLogResponse } from '@/lib/api/errorLog'
import { useUIStore } from '@/store/ui'

const KEY = ['errorLog']

export function useErrorLog() {
  return useQuery<ErrorLogResponse>({
    queryKey: KEY,
    queryFn: () => getErrorLog(),
    refetchInterval: 10_000,
    retry: 1,
  })
}

export function useClearErrorLog() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: clearErrorLog,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

/** Count of records newer than the last time the Error Log page was opened. */
export function useErrorBadge(): number {
  const { data } = useErrorLog()
  const seenAt = useUIStore((s) => s.errorsSeenAt)
  if (!data) return 0
  return data.items.filter((e) => Date.parse(e.lastTs) > seenAt).length
}
