import { useState, type FormEvent } from 'react'
import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useRunWorkflow } from '@/hooks/useRunWorkflow'

/** First 8 chars of a workflow id, for a compact inline reference. */
function shortId(id: string): string {
  return id.length > 8 ? id.slice(0, 8) : id
}

/**
 * RunTask — a compact on-brand control to dispatch a task to the CEO agent.
 * A styled glass input plus an "Assign to CEO" button (useRunWorkflow). Shows a
 * small inline status line for the latest run: status + short workflow id, and an
 * "awaiting approval" hint when the run is gated.
 */
export function RunTask() {
  const [task, setTask] = useState('')
  const { mutate, data, isPending, isError } = useRunWorkflow()

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = task.trim()
    if (!trimmed || isPending) return
    mutate({ task: trimmed })
  }

  const gated = data?.status === 'awaiting_approval'

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
        <Button type="submit" size="sm" disabled={isPending || task.trim().length === 0}>
          <Sparkles aria-hidden />
          {isPending ? 'Assigning…' : 'Assign to CEO'}
        </Button>
      </div>

      {(data || isError) && (
        <p className="text-xs text-[#a1a1aa]" role="status" aria-live="polite">
          {isError && <span className="text-omnivra-pink">Could not reach the company. Try again.</span>}
          {data && (
            <>
              <span
                className={cn(
                  'font-medium',
                  gated ? 'text-omnivra-amber' : 'text-omnivra-emerald',
                )}
              >
                {data.status}
              </span>
              <span className="text-[#71717a]"> · {shortId(data.workflowId)}</span>
              {gated && <span className="text-omnivra-amber"> — awaiting approval</span>}
            </>
          )}
        </p>
      )}
    </form>
  )
}
