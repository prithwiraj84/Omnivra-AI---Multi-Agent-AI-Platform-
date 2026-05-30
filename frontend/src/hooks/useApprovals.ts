/**
 * Approval-gate hooks (Phase 7).
 *  - useAwaitingApprovals(): polls the resumable/recovery set (runs paused on the gate).
 *  - useApprovalDecision(): resolves a paused run, then refreshes the awaiting set + dashboard.
 * Queries fail gracefully offline (jsdom/tests) — consumers should default to [] on no data.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { decideApproval, listAwaitingRuns, type ApprovalAction } from '@/lib/api/workflows'
import type { RunResult } from '@/lib/api/types'

/** Live awaiting runs — polled every 8s; one retry so an offline host settles quickly. */
export function useAwaitingApprovals() {
  return useQuery<RunResult[]>({
    queryKey: ['approvals', 'awaiting'],
    queryFn: listAwaitingRuns,
    refetchInterval: 8000,
    retry: 1,
  })
}

interface DecisionVars {
  approvalId: string
  action: ApprovalAction
  note?: string
}

/** Submit an approval decision; on success refresh the awaiting set and the dashboard cache. */
export function useApprovalDecision() {
  const qc = useQueryClient()
  return useMutation<RunResult, Error, DecisionVars>({
    mutationFn: ({ approvalId, action, note }) => decideApproval(approvalId, action, note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['approvals', 'awaiting'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}
