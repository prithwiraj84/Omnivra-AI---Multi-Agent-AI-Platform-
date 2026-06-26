/**
 * Department command-center API (cp-0048). Uses the shared axios instance.
 */
import { api } from '@/lib/api/client'
import type { DepartmentOverview } from '@/lib/api/types'

/** Aggregated command-center data for one department. GET /departments/{slug}/overview. */
export async function getDepartmentOverview(slug: string): Promise<DepartmentOverview> {
  const { data } = await api.get<DepartmentOverview>(`/departments/${slug}/overview`)
  return data
}
