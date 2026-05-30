import { ShieldCheck } from 'lucide-react'
import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { ApprovalCard, type ApprovalAction } from '@/components/dashboard/approval-card'
import { useAwaitingApprovals, useApprovalDecision } from '@/hooks/useApprovals'
import type { RunResult } from '@/lib/api/types'
import type { ApprovalItem } from '@/types'

export interface PendingApprovalsProps {
  items: ApprovalItem[]
  total: number
  onReview?: (id: string) => void
}

/** Map a paused (awaiting) run into the ApprovalItem display shape. */
function runToApprovalItem(run: RunResult): ApprovalItem {
  const pending = run.pendingApproval
  return {
    id: run.workflowId,
    title: pending?.summary || run.task,
    source: pending ? `by ${pending.requestedBy}` : run.task,
    priority: 'high',
    icon: ShieldCheck,
    accent: 'amber',
  }
}

/**
 * PendingApprovals — the right-rail "Pending Approvals" panel. Renders LIVE awaiting
 * runs (the resumable/recovery set, from useAwaitingApprovals) wired to the approval
 * gate ABOVE the seed `items`, then the seed items below. The footer total counts both.
 * Offline (tests), the live query yields no data → the card looks exactly as before.
 */
export function PendingApprovals({ items, total, onReview }: PendingApprovalsProps) {
  const { data: awaiting } = useAwaitingApprovals()
  const decision = useApprovalDecision()

  const liveRuns = awaiting ?? []
  const pendingId = decision.isPending ? decision.variables?.approvalId : undefined

  return (
    <GlassCard padding="md">
      <SectionHeader
        label="Pending Approvals"
        action={
          <button
            type="button"
            className="text-xs font-medium text-omnivra-cyan transition-colors hover:brightness-110"
          >
            View All
          </button>
        }
        className="mb-4"
      />

      {liveRuns.length > 0 && (
        <p className="mb-3 text-xs text-omnivra-amber">
          {liveRuns.length} live awaiting
        </p>
      )}

      <div className="flex flex-col gap-3">
        {liveRuns.map((run) => {
          const approvalId = run.pendingApproval?.approvalId
          const busy = approvalId !== undefined && pendingId === approvalId
          return (
            <ApprovalCard
              key={run.workflowId}
              item={runToApprovalItem(run)}
              busy={busy}
              onDecision={(action: ApprovalAction) => {
                if (approvalId) decision.mutate({ approvalId, action })
              }}
            />
          )
        })}

        {items.map((item) => (
          <ApprovalCard key={item.id} item={item} onReview={onReview} />
        ))}
      </div>

      <p className="mt-4 text-right text-xs text-zinc-400">
        Total Pending:{' '}
        <span className="tabular font-medium text-zinc-200">{total + liveRuns.length}</span>
      </p>
    </GlassCard>
  )
}
