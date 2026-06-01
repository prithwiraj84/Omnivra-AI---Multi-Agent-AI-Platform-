import { useMemo, useState } from 'react'
import { GitBranch, Workflow as WorkflowIcon } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { StatusDot } from '@/components/ui/status-dot'
import { EmptyState } from '@/components/ui/empty-state'
import { ScrollArea } from '@/components/ui/scroll-area'
import { RunTask } from '@/components/dashboard/run-task'
import { WorkflowList } from '@/components/dashboard/workflow-list'
import { RecoveryStatus } from '@/components/dashboard/recovery-status'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { useActiveWorkflows, useWorkflowRuns } from '@/hooks/useWorkflowRuns'
import { useDashboard } from '@/hooks/useDashboard'
import { cn } from '@/lib/utils'
import type { AgentRunOutput, RunResult, RunStatus } from '@/lib/api/types'

/** First 8 chars of a workflow id, for a compact inline reference. */
function shortId(id: string): string {
  return id.length > 8 ? id.slice(0, 8) : id
}

/** Run status → NeonBadge tone + human label. */
const STATUS_META: Record<RunStatus, { tone: BadgeTone; label: string }> = {
  running: { tone: 'info', label: 'running' },
  completed: { tone: 'success', label: 'completed' },
  failed: { tone: 'danger', label: 'failed' },
  stopped: { tone: 'danger', label: 'stopped' },
  awaiting_approval: { tone: 'warning', label: 'awaiting approval' },
  rolled_back: { tone: 'info', label: 'rolled back' },
}

/** Collect the artifact paths a run produced, from its `result` bag (best-effort). */
function artifactPaths(result: Record<string, unknown>): string[] {
  const raw = result.artifacts ?? result.files
  if (Array.isArray(raw)) {
    return raw.filter((p): p is string => typeof p === 'string')
  }
  return []
}

/** One agent's contribution inside an expanded run. */
function AgentOutputRow({ output }: { output: AgentRunOutput }) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
      <StatusDot status={output.ok ? 'online' : 'offline'} className="mt-1" />
      <div className="min-w-0 flex-1">
        <p className="truncate font-mono text-xs font-medium text-[#e4e4e7]">{output.agentId}</p>
        <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-[#a1a1aa]">
          {output.content || '(no output)'}
        </p>
      </div>
      {output.tokens > 0 && (
        <span className="tabular shrink-0 text-[10px] text-[#71717a]">{output.tokens} tok</span>
      )}
    </div>
  )
}

/** A single run-history row: header line + an expanded detail body when selected. */
function RunRow({
  run,
  expanded,
  onToggle,
}: {
  run: RunResult
  expanded: boolean
  onToggle: () => void
}) {
  // Fallback for any status the backend emits but the type map doesn't enumerate (free-form
  // RunResult.status on the wire) — never let an unknown status crash the run-history list.
  const meta = STATUS_META[run.status] ?? { tone: 'info' as BadgeTone, label: run.status }
  const artifacts = artifactPaths(run.result)

  return (
    <div className="py-1">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className={cn(
          'flex w-full items-center gap-3 rounded-lg border border-transparent px-2.5 py-2.5 text-left transition-colors',
          'hover:bg-white/[0.04]',
          expanded && 'border-white/10 bg-white/[0.05]',
        )}
      >
        <GitBranch className="h-4 w-4 shrink-0 text-omnivra-cyan" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-[#e4e4e7]">{run.task}</p>
          <p className="mt-0.5 flex items-center gap-2 text-xs text-[#71717a]">
            <span className="font-mono">{shortId(run.workflowId)}</span>
            <span aria-hidden>·</span>
            <span className="tabular">{run.agentOutputs.length} agents</span>
            <span aria-hidden>·</span>
            <span className="tabular">depth {run.recursionCount}</span>
          </p>
        </div>
        <NeonBadge tone={meta.tone} className="shrink-0 capitalize">
          {meta.label}
        </NeonBadge>
      </button>

      {expanded && (
        <div className="mt-2 flex flex-col gap-2 px-2.5 pb-2">
          {run.agentOutputs.length > 0 ? (
            run.agentOutputs.map((output) => (
              <AgentOutputRow key={output.agentId} output={output} />
            ))
          ) : (
            <p className="px-1 text-xs text-[#71717a]">No agent outputs recorded for this run.</p>
          )}

          {artifacts.length > 0 && (
            <div className="mt-1 flex flex-col gap-1 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
              <p className="section-label">Artifacts</p>
              {artifacts.map((path) => (
                <p key={path} className="truncate font-mono text-xs text-[#a1a1aa]">
                  {path}
                </p>
              ))}
            </div>
          )}

          {run.errors.length > 0 && (
            <div className="flex flex-col gap-1 rounded-lg border border-omnivra-pink/20 bg-omnivra-pink/[0.06] p-3">
              <p className="section-label text-omnivra-pink">Errors</p>
              {run.errors.map((err, i) => (
                <p key={i} className="text-xs leading-relaxed text-omnivra-pink">
                  {err}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Workflows — the operations page. Top: a RunTask control to dispatch a task to
 * the CEO. Below, a two-column layout: LEFT the active/seed workflows (live from
 * the API, falling back to the dashboard seed when empty); RIGHT the run history,
 * each row expandable to reveal its agent outputs, artifacts and errors. Polls the
 * run history every 8s; offline it shows the empty state rather than crashing.
 */
export function Workflows() {
  const dashboard = useDashboard()
  const { data: activeWorkflows } = useActiveWorkflows()
  const { data: runs } = useWorkflowRuns()
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const workflows = useMemo(() => {
    const live = activeWorkflows ?? []
    return live.length > 0 ? live : dashboard.data.workflows
  }, [activeWorkflows, dashboard.data.workflows])

  const runList = runs ?? []

  return (
    <div className="flex flex-col gap-6">
      <Reveal>
        <GlassCard padding="lg">
          <SectionHeader label="Run a Workflow" />
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-[#a1a1aa]">
            Assign a task to the CEO agent. It plans the work, delegates to the right
            departments, and pauses on the approval gate when a decision needs your sign-off.
          </p>
          <RunTask />
        </GlassCard>
      </Reveal>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Reveal delay={0.05}>
          <WorkflowList workflows={workflows} />
        </Reveal>

        <Reveal delay={0.1}>
          <GlassCard padding="none" className="overflow-hidden">
            <div className="border-b border-white/5 p-5">
              <SectionHeader label="Run History" count={runList.length} />
            </div>

            {runList.length === 0 ? (
              <EmptyState
                icon={WorkflowIcon}
                title="No runs yet"
                hint="Assign a task to generate runs — each one lands here with its full agent breakdown."
                className="py-16"
              />
            ) : (
              <ScrollArea className="max-h-[34rem]">
                <Stagger className="flex flex-col p-3">
                  {runList.map((run) => (
                    <StaggerItem key={run.workflowId}>
                      <RunRow
                        run={run}
                        expanded={expandedId === run.workflowId}
                        onToggle={() =>
                          setExpandedId((cur) =>
                            cur === run.workflowId ? null : run.workflowId,
                          )
                        }
                      />
                    </StaggerItem>
                  ))}
                </Stagger>
              </ScrollArea>
            )}
          </GlassCard>
        </Reveal>
      </div>

      <Reveal delay={0.15}>
        <RecoveryStatus />
      </Reveal>
    </div>
  )
}
