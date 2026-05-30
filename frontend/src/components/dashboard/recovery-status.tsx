import { Link } from 'react-router-dom'
import { ArrowUpRight, GitCommit, LifeBuoy, PauseCircle } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { StatusDot } from '@/components/ui/status-dot'
import { EmptyState } from '@/components/ui/empty-state'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useWorkflowRuns } from '@/hooks/useWorkflowRuns'
import { useCheckpoints } from '@/hooks/useSystem'
import type { Checkpoint } from '@/lib/api/system'
import type { RunResult } from '@/lib/api/types'

/** First 8 chars of an id, for a compact inline reference. */
function shortId(id: string): string {
  return id.length > 8 ? id.slice(0, 8) : id
}

/** True once a checkpoint has been committed (its work is durably recorded). */
function isCommitted(status: string): boolean {
  return status.toLowerCase() === 'committed'
}

/** One awaiting-approval run: short id + task + a deep-link back to Approvals. */
function ResumableRow({ run }: { run: RunResult }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-omnivra-amber/20 bg-omnivra-amber/[0.05] p-3">
      <PauseCircle className="h-4 w-4 shrink-0 text-omnivra-amber" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-[#e4e4e7]">{run.task}</p>
        <p className="mt-0.5 truncate font-mono text-xs text-[#71717a]">
          {shortId(run.workflowId)}
        </p>
      </div>
      <Link
        to="/approvals"
        className="focus-ring inline-flex shrink-0 items-center gap-1 rounded-md text-xs font-medium text-omnivra-cyan transition-colors hover:brightness-110"
      >
        Resume in Approvals
        <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
      </Link>
    </div>
  )
}

/** One node in the compact checkpoint timeline: committed dot + id + phase title. */
function CheckpointNode({ checkpoint, last }: { checkpoint: Checkpoint; last: boolean }) {
  const committed = isCommitted(checkpoint.status)
  return (
    <li className="relative flex gap-3 pl-1">
      {/* connector spine */}
      {!last && (
        <span
          className="absolute left-[6px] top-5 h-[calc(100%-0.25rem)] w-px bg-white/10"
          aria-hidden
        />
      )}
      <span className="relative z-10 mt-1 flex h-3 w-3 items-center justify-center">
        <StatusDot status={committed ? 'online' : 'idle'} pulse={committed} />
      </span>
      <div className="min-w-0 flex-1 pb-3">
        <p className="truncate text-sm font-medium text-[#e4e4e7]">{checkpoint.phaseTitle}</p>
        <p className="mt-0.5 flex items-center gap-2 truncate text-xs text-[#71717a]">
          <span className="font-mono">{checkpoint.id}</span>
          <span aria-hidden>·</span>
          <span className="capitalize">{checkpoint.status}</span>
        </p>
      </div>
    </li>
  )
}

/**
 * RecoveryStatus — the Recovery detail panel (DESIGN_SYSTEM 8.3). Surfaces what the
 * Recovery agent can pick back up: (a) resumable runs paused on the approval gate
 * (useWorkflowRuns("awaiting_approval")) as a short list deep-linking to /approvals,
 * and (b) the cp-NNNN checkpoint lineage (useCheckpoints) as a compact vertical
 * timeline with a committed StatusDot per node. Shows an EmptyState when there's
 * neither. Reduced-motion-safe (no entrance animation here; StatusDot's pulse is the
 * only motion and respects the global prefers-reduced-motion). Offline the queries
 * never resolve and the EmptyState renders without crashing.
 */
export function RecoveryStatus() {
  const { data: awaiting } = useWorkflowRuns('awaiting_approval')
  const { data: checkpoints } = useCheckpoints()

  const resumable = awaiting ?? []
  const lineage = checkpoints ?? []
  const empty = resumable.length === 0 && lineage.length === 0

  return (
    <GlassCard padding="none" className="overflow-hidden">
      <div className="border-b border-white/5 p-5">
        <SectionHeader label="Recovery" count={resumable.length} />
      </div>

      {empty ? (
        <EmptyState
          icon={LifeBuoy}
          title="Nothing to recover"
          hint="No runs are paused for approval and no checkpoints have been recorded yet."
          className="py-14"
        />
      ) : (
        <div className="flex flex-col gap-5 p-5">
          {resumable.length > 0 && (
            <section className="flex flex-col gap-2.5">
              <span className="section-label">Resumable Runs</span>
              <ScrollArea className="max-h-[16rem]">
                <div className="flex flex-col gap-2">
                  {resumable.map((run) => (
                    <ResumableRow key={run.workflowId} run={run} />
                  ))}
                </div>
              </ScrollArea>
            </section>
          )}

          {lineage.length > 0 && (
            <section className="flex flex-col gap-3">
              <div className="flex items-center gap-1.5">
                <GitCommit className="h-3.5 w-3.5 text-omnivra-cyan" aria-hidden />
                <span className="section-label">Checkpoint Lineage</span>
              </div>
              <ScrollArea className="max-h-[20rem]">
                <ol className="flex flex-col">
                  {lineage.map((cp, i) => (
                    <CheckpointNode
                      key={cp.id}
                      checkpoint={cp}
                      last={i === lineage.length - 1}
                    />
                  ))}
                </ol>
              </ScrollArea>
            </section>
          )}
        </div>
      )}
    </GlassCard>
  )
}
