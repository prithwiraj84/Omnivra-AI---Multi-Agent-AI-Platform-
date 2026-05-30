/**
 * useRunWorkflow — kick off a workflow run from the UI (Phase 7). On success it
 * invalidates the awaiting-approvals set so a freshly gated run shows up in the
 * recovery view immediately.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { runWorkflow } from '@/lib/api/workflows'
import type { RunResult } from '@/lib/api/types'

interface RunVars {
  task: string
}

export function useRunWorkflow() {
  const qc = useQueryClient()
  return useMutation<RunResult, Error, RunVars>({
    mutationFn: ({ task }) => runWorkflow(task),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['approvals', 'awaiting'] })
    },
  })
}
