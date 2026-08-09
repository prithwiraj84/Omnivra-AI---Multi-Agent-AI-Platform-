/**
 * useDashboard — the single source of dashboard data for the UI.
 * Renders instantly from the bundled fallback (initialData), then upgrades to live
 * backend data from GET /api/dashboard. If the backend is down (or in tests), it
 * stays on the fallback — the UI never blanks out.
 *
 * `initialDataUpdatedAt: 0` marks the bundled fallback as immediately stale, so the
 * real backend data is fetched on mount (otherwise staleTime would treat the dummy
 * fallback as fresh and skip the fetch). `refetchInterval` keeps the dashboard live.
 */
import { useQuery } from '@tanstack/react-query'
import { getDashboard } from '@/lib/api/dashboard'
import type { DashboardData } from '@/lib/api/types'
import { fallbackDashboard } from '@/data/dashboard'

export function useDashboard() {
  return useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
    initialData: fallbackDashboard,
    initialDataUpdatedAt: 0, // fallback is stale on arrival -> fetch real data immediately
    staleTime: 3_000,
    // Poll FAST (3s) while work is visibly in flight, and still reasonably fast (6s) when it
    // isn't. The idle interval matters more than it looks: the "active" test below can only see
    // work the PREVIOUS response reported, so a long idle interval delays the very transition
    // it is watching for — an agent could start and finish a document inside one 15s gap and
    // never once appear as working. The WebSocket 'agent_activity' event (useWebSocket) is the
    // real-time path; this is the floor for when the socket is down or unsupported.
    refetchInterval: (query) => {
      const d = query.state.data
      const active =
        !!d?.agents?.some((a) => a.status === 'working' || a.status === 'needs_approval') ||
        !!d?.workflows?.some((w) => w.status === 'In Progress' || w.status === 'Review')
      return active ? 3_000 : 6_000
    },
    retry: 1,
  })
}
