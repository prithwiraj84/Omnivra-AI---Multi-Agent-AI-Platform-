/**
 * Workflow + approval-gate API calls (Phase 7). Uses the shared `@/lib/api/client`
 * axios instance (baseURL '/api'). All responses are the camelCase RunResult wire shape.
 */
import { api } from '@/lib/api/client'
import { resolveIcon } from '@/lib/api/icons'
import type { RunResult, WorkflowDTO } from '@/lib/api/types'
import type { WorkflowItem } from '@/types'

/** Approval-gate decision actions. */
export type ApprovalAction = 'approve' | 'reject' | 'retry' | 'rollback'

/**
 * Kick off a workflow run. POST /workflows/run. Runs in the active project (sent as
 * the X-Project-Id header by the axios interceptor). If the task is gated, the
 * returned RunResult has status 'awaiting_approval' and a non-null `pendingApproval`.
 */
export async function runWorkflow(task: string): Promise<RunResult> {
  const { data } = await api.post<RunResult>('/workflows/run', { task })
  return data
}

/** Resumable/recovery set: runs paused on the approval gate. GET /workflows/runs?status=awaiting_approval. */
export async function listAwaitingRuns(): Promise<RunResult[]> {
  const { data } = await api.get<RunResult[]>('/workflows/runs', {
    params: { status: 'awaiting_approval' },
  })
  return data
}

/**
 * The full run history. GET /workflows/runs. Pass an optional `status`
 * (completed | failed | awaiting_approval | rolled_back) to filter server-side.
 */
export async function listRuns(status?: string): Promise<RunResult[]> {
  const { data } = await api.get<RunResult[]>('/workflows/runs', {
    params: status ? { status } : undefined,
  })
  return data
}

/** A single run by its workflow id. GET /workflows/runs/{id}. */
export async function getRun(id: string): Promise<RunResult> {
  const { data } = await api.get<RunResult>(`/workflows/runs/${id}`)
  return data
}

/**
 * The active/seed workflows. GET /workflows. The wire form carries a string
 * `icon` key, so we resolve it to a Lucide component for the UI (mirrors the
 * dashboard adapter).
 */
export async function listActiveWorkflows(): Promise<WorkflowItem[]> {
  const { data } = await api.get<WorkflowDTO[]>('/workflows')
  return data.map((w) => ({ ...w, icon: resolveIcon(w.icon) }))
}

/**
 * Resolve a paused run. POST /approvals/{approvalId}/decision. approve/retry ->
 * 'completed', reject -> 'failed', rollback -> 'rolled_back'. Returns the resumed run.
 */
export async function decideApproval(
  approvalId: string,
  action: ApprovalAction,
  note?: string,
): Promise<RunResult> {
  const { data } = await api.post<RunResult>(`/approvals/${approvalId}/decision`, { action, note })
  return data
}
