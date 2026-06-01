import { useState, type FormEvent } from 'react'
import { Loader2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useRunWorkflow } from '@/hooks/useRunWorkflow'
import { useWorkflowRun } from '@/hooks/useWorkflowRuns'

/** First 8 chars of a workflow id, for a compact inline reference. */
function shortId(id: string): string {
  return id.length > 8 ? id.slice(0, 8) : id
}

/**
 * RunTask — dispatch a task to the CEO agent and track it to completion.
 *
 * A real multi-agent run takes many seconds, so the backend returns a 'running' record
 * immediately and runs the graph in the background; we poll the run (useWorkflowRun) until it
 * reaches a terminal status. The inline status line reflects: working… → completed / awaiting
 * approval / failed, with a short workflow id. (Previously the UI awaited the whole run and
 * timed out — "Could not reach the company".)
 */
export function RunTask() {
  const [task, setTask] = useState('')
  const [runId, setRunId] = useState<string | null>(null)
  const run = useRunWorkflow()
  const polled = useWorkflowRun(runId)

  // The dispatch response (running) until the first poll lands, then the live polled run.
  const result = polled.data ?? run.data
  const status = result?.status
  // The poll self-heals transient blips (refetchInterval keeps firing while status is undefined),
  // but a SUSTAINED failure must not wedge the form on 'Working…' forever with no signal: treat an
  // errored poll that never produced terminal data as a dead-end so we re-enable the input and show
  // an error, rather than trusting the stale 'running' dispatch response indefinitely.
  const pollFailed = !!runId && polled.isError && !polled.data
  const working = !pollFailed && (run.isPending || (!!runId && (status === undefined || status === 'running')))
  const gated = status === 'awaiting_approval'

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = task.trim()
    if (!trimmed || working) return
    run.mutate(
      { task: trimmed },
      {
        onSuccess: (r) => {
          setRunId(r.workflowId)
          setTask('')
        },
      },
    )
  }

  const tone =
    status === 'completed'
      ? 'text-omnivra-emerald'
      : gated
        ? 'text-omnivra-amber'
        : status === 'failed'
          ? 'text-omnivra-pink'
          : 'text-omnivra-cyan'

  return (
    <form onSubmit={submit} className="mt-1 flex max-w-xl flex-col gap-1.5">
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={task}
          onChange={(e) => setTask(e.target.value)}
          placeholder="Assign a task to your AI company…"
          aria-label="Task to assign to the CEO agent"
          className="focus-ring h-9 flex-1 rounded-md bg-omnivra-surface-2 px-3 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
        />
        <Button type="submit" size="sm" disabled={working || task.trim().length === 0}>
          {working ? <Loader2 className="animate-spin" aria-hidden /> : <Sparkles aria-hidden />}
          {working ? 'Working…' : 'Assign to CEO'}
        </Button>
      </div>

      {(result || run.isError || pollFailed) && (
        <p className="text-xs text-[#a1a1aa]" role="status" aria-live="polite">
          {(run.isError || pollFailed) && (
            <span className="text-omnivra-pink">Could not reach the company. Try again.</span>
          )}
          {result && !pollFailed && (
            <>
              <span className={cn('font-medium', tone)}>{working ? 'working' : status}</span>
              <span className="text-[#71717a]"> · {shortId(result.workflowId)}</span>
              {gated && <span className="text-omnivra-amber"> — awaiting approval</span>}
            </>
          )}
        </p>
      )}
    </form>
  )
}
