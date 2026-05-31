import { useState, type FormEvent } from 'react'
import {
  CheckCircle2,
  CircleDashed,
  Eye,
  ListChecks,
  Loader2,
  Plus,
  Trash2,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { Chip } from '@/components/ui/chip'
import { IconButton } from '@/components/ui/icon-button'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import { cn } from '@/lib/utils'
import { useProjects } from '@/hooks/useProjects'
import { useCreateTask, useDeleteTask, useTasks, useUpdateTask } from '@/hooks/useTasks'
import { useProjectStore } from '@/store/project'
import type { Accent } from '@/types'
import type { Task } from '@/lib/api/types'

/** Ordered Kanban columns: backend status → display label + column accent/icon. */
const COLUMNS: { status: string; label: string; accent: Accent; icon: LucideIcon }[] = [
  { status: 'todo', label: 'To Do', accent: 'cyan', icon: CircleDashed },
  { status: 'in_progress', label: 'In Progress', accent: 'blue', icon: Loader2 },
  { status: 'review', label: 'Review', accent: 'amber', icon: Eye },
  { status: 'done', label: 'Done', accent: 'emerald', icon: CheckCircle2 },
]

const STATUS_ORDER = COLUMNS.map((c) => c.status)

/** Priority → NeonBadge tone (high=danger, medium=warning, low=info). */
function priorityTone(priority: string): BadgeTone {
  switch (priority) {
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    default:
      return 'info'
  }
}

/** Literal accent text classes for the column header label (Tailwind scanner-safe). */
const headerText: Record<Accent, string> = {
  cyan: 'text-omnivra-cyan',
  violet: 'text-omnivra-purple',
  blue: 'text-omnivra-blue',
  emerald: 'text-omnivra-emerald',
  amber: 'text-omnivra-amber',
  pink: 'text-omnivra-pink',
}

/** One task card: title, priority badge, optional agent chip + quick move/delete controls. */
function TaskCard({ task, onMove, onDelete, busy }: {
  task: Task
  onMove: (id: string, status: string) => void
  onDelete: (id: string) => void
  busy: boolean
}) {
  const idx = STATUS_ORDER.indexOf(task.status)
  const prev = idx > 0 ? STATUS_ORDER[idx - 1] : null
  const next = idx >= 0 && idx < STATUS_ORDER.length - 1 ? STATUS_ORDER[idx + 1] : null
  const prevLabel = prev ? COLUMNS[idx - 1].label : ''
  const nextLabel = next ? COLUMNS[idx + 1].label : ''

  return (
    <div className="flex flex-col gap-2.5 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
      <div className="flex items-start justify-between gap-2">
        <p className="min-w-0 flex-1 text-sm font-medium leading-snug text-[#e4e4e7]">{task.title}</p>
        <IconButton
          icon={Trash2}
          aria-label={`Delete task ${task.title}`}
          onClick={() => onDelete(task.id)}
          disabled={busy}
          className="-mr-1 -mt-1 h-7 w-7 hover:text-omnivra-red"
        />
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <NeonBadge tone={priorityTone(task.priority)}>{task.priority}</NeonBadge>
        {task.agentId && <Chip label={task.agentId} accent="cyan" />}
      </div>

      <div className="flex items-center gap-1.5 pt-0.5">
        <Button
          type="button"
          size="sm"
          variant="ghost"
          disabled={!prev || busy}
          onClick={() => prev && onMove(task.id, prev)}
          className="h-7 flex-1 px-2 text-[11px]"
          aria-label={prev ? `Move ${task.title} to ${prevLabel}` : undefined}
        >
          ← {prevLabel || 'Back'}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={!next || busy}
          onClick={() => next && onMove(task.id, next)}
          className="h-7 flex-1 px-2 text-[11px]"
          aria-label={next ? `Move ${task.title} to ${nextLabel}` : undefined}
        >
          {nextLabel || 'Done'} →
        </Button>
      </div>
    </div>
  )
}

/** One Kanban column: a glass panel listing every task in one status. */
function Column({ column, tasks, onMove, onDelete, busyId }: {
  column: (typeof COLUMNS)[number]
  tasks: Task[]
  onMove: (id: string, status: string) => void
  onDelete: (id: string) => void
  busyId: string | undefined
}) {
  const { label, accent, icon: Icon } = column
  return (
    <GlassCard padding="none" className="flex min-h-[18rem] flex-col overflow-hidden">
      <div className="flex items-center justify-between gap-2 border-b border-white/5 p-3.5">
        <div className={cn('flex items-center gap-2 text-xs font-semibold uppercase tracking-wide', headerText[accent])}>
          <Icon className="h-4 w-4 shrink-0" aria-hidden />
          <span>{label}</span>
        </div>
        <span className="tabular inline-flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-white/[0.06] px-1.5 text-[10px] font-semibold leading-none text-[#a1a1aa]">
          {tasks.length}
        </span>
      </div>

      {tasks.length === 0 ? (
        <EmptyState icon={ListChecks} title="No tasks" className="flex-1 py-10" />
      ) : (
        <ScrollArea className="max-h-[30rem] flex-1">
          <Stagger className="flex flex-col gap-2.5 p-3">
            {tasks.map((task) => (
              <StaggerItem key={task.id}>
                <TaskCard
                  task={task}
                  onMove={onMove}
                  onDelete={onDelete}
                  busy={busyId === task.id}
                />
              </StaggerItem>
            ))}
          </Stagger>
        </ScrollArea>
      )}
    </GlassCard>
  )
}

/**
 * Tasks — a Kanban board with four columns (To Do / In Progress / Review / Done),
 * each a GlassCard listing that status's tasks as compact cards (title, a priority
 * NeonBadge, the agentId as a Chip when present). A create row (title input + a
 * project select from useProjects + "Add Task") creates tasks via useCreateTask.
 * Each card has Move ←/→ controls (useUpdateTask) and a delete IconButton
 * (useDeleteTask). Columns stack on small screens. Offline (jsdom/tests) the
 * queries never resolve and every column shows its empty state.
 */
export function Tasks() {
  const [title, setTitle] = useState('')
  const [projectId, setProjectId] = useState('')
  const activeProjectId = useProjectStore((s) => s.activeProjectId)

  // The board scopes to the active project (switching projects refetches via the key).
  const { data: tasks } = useTasks(activeProjectId)
  const { data: projects } = useProjects()
  const create = useCreateTask()
  const update = useUpdateTask()
  const remove = useDeleteTask()

  const list = tasks ?? []
  const projectList = projects ?? []

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed || create.isPending) return
    create.mutate(
      // Default to the active project so the new task lands on the scoped board.
      { title: trimmed, projectId: projectId || activeProjectId },
      { onSuccess: () => setTitle('') },
    )
  }

  const onMove = (id: string, status: string) => update.mutate({ id, patch: { status } })
  const onDelete = (id: string) => remove.mutate(id)

  // The card actively mutating (move or delete) — used to disable that card's controls.
  const busyId =
    (update.isPending ? update.variables?.id : undefined) ??
    (remove.isPending ? remove.variables : undefined)

  return (
    <div className="flex flex-col gap-5">
      <GlassCard padding="none" className="overflow-hidden">
        <div className="flex flex-col gap-4 p-5">
          <SectionHeader label="Tasks" count={list.length} />

          <form onSubmit={submit} className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="New task title…"
              aria-label="New task title"
              className="focus-ring h-9 flex-1 rounded-md bg-omnivra-surface-2 px-3 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
            />
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              aria-label="Project for the new task"
              className="focus-ring h-9 rounded-md bg-omnivra-surface-2 px-3 text-sm text-[#e4e4e7] transition-colors duration-200 ease-out-quint sm:w-52"
            >
              <option value="">No project</option>
              {projectList.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <Button type="submit" size="sm" disabled={create.isPending || title.trim().length === 0}>
              <Plus aria-hidden />
              {create.isPending ? 'Adding…' : 'Add Task'}
            </Button>
          </form>

          {create.isError && (
            <p className="text-xs text-omnivra-pink" role="status" aria-live="polite">
              Could not create the task. Try again.
            </p>
          )}
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {COLUMNS.map((column) => (
          <Column
            key={column.status}
            column={column}
            tasks={list.filter((t) => t.status === column.status)}
            onMove={onMove}
            onDelete={onDelete}
            busyId={busyId}
          />
        ))}
      </div>
    </div>
  )
}
