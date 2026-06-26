/**
 * useDepartmentOverview — live command-center data for one department. Polls fast (3s)
 * while any of its agents is working/awaiting, else every 15s. Fails gracefully offline.
 */
import { useQuery } from '@tanstack/react-query'
import { getDepartmentOverview } from '@/lib/api/departments'
import type { DepartmentOverview } from '@/lib/api/types'

export function useDepartmentOverview(slug: string) {
  return useQuery<DepartmentOverview>({
    queryKey: ['department', slug],
    queryFn: () => getDepartmentOverview(slug),
    enabled: !!slug,
    staleTime: 3_000,
    refetchInterval: (query) =>
      query.state.data?.agents?.some((a) => a.status === 'working' || a.status === 'needs_approval')
        ? 3_000
        : 15_000,
    retry: 1,
  })
}
