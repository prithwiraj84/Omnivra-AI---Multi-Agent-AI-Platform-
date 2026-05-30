/**
 * useDashboard — the single source of dashboard data for the UI.
 * Renders instantly from the bundled fallback (initialData), then upgrades to live
 * backend data from GET /api/dashboard when the API responds. If the backend is down
 * (or in tests), it stays on the fallback — the UI never blanks out.
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
    staleTime: 30_000,
    retry: 1,
  })
}
