/**
 * Workflow run-history + active-workflow hooks (Cluster B).
 *  - useWorkflowRuns(status?): polls the run history (optionally filtered by status).
 *  - useActiveWorkflows(): the active/seed workflows (icon-resolved).
 * Both fail gracefully offline (jsdom/tests) — consumers default to [] and render
 * the empty state rather than crashing.
 */
import { useQuery } from '@tanstack/react-query'
import { listActiveWorkflows, listRuns } from '@/lib/api/workflows'
import type { RunResult } from '@/lib/api/types'
import type { WorkflowItem } from '@/types'

/** Run history — polled every 8s; one retry so an offline host settles quickly. */
export function useWorkflowRuns(status?: string) {
  return useQuery<RunResult[]>({
    queryKey: ['workflows', 'runs', status],
    queryFn: () => listRuns(status),
    refetchInterval: 8000,
    retry: 1,
  })
}

/** Active/seed workflows — one retry so an offline host settles quickly. */
export function useActiveWorkflows() {
  return useQuery<WorkflowItem[]>({
    queryKey: ['workflows', 'active'],
    queryFn: listActiveWorkflows,
    retry: 1,
  })
}
