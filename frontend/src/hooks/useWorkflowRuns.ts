/**
 * Workflow run-history + active-workflow hooks (Cluster B).
 *  - useWorkflowRuns(status?): polls the run history (optionally filtered by status).
 *  - useActiveWorkflows(): the active/seed workflows (icon-resolved).
 * Both fail gracefully offline (jsdom/tests) — consumers default to [] and render
 * the empty state rather than crashing.
 */
import { useQuery } from '@tanstack/react-query'
import { getRun, listActiveWorkflows, listRuns } from '@/lib/api/workflows'
import type { RunResult } from '@/lib/api/types'
import type { WorkflowItem } from '@/types'
import { useProjectStore } from '@/store/project'

/** Run history — polled every 8s; scoped to the active project. */
export function useWorkflowRuns(status?: string) {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<RunResult[]>({
    queryKey: ['workflows', 'runs', projectId, status],
    queryFn: () => listRuns(status),
    refetchInterval: 8000,
    retry: 1,
  })
}

/**
 * Poll ONE run until it reaches a terminal status. Used by RunTask after dispatching a
 * task: the POST returns a 'running' record, then we poll GET /workflows/runs/{id} every
 * 2s until status leaves 'running' (completed / awaiting_approval / failed), then stop.
 */
export function useWorkflowRun(workflowId: string | null) {
  return useQuery<RunResult>({
    queryKey: ['workflows', 'run', workflowId],
    queryFn: () => getRun(workflowId as string),
    enabled: !!workflowId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status && status !== 'running' ? false : 2000
    },
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
