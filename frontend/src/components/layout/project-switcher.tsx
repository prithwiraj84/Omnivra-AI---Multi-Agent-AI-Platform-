import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Check, ChevronsUpDown, FolderKanban, FolderPlus, Loader2, Trash2, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useCreateProject, useDeleteProject, useProjects } from '@/hooks/useProjects'
import { DEFAULT_PROJECT_ID, useProjectStore } from '@/store/project'

/**
 * ProjectSwitcher — the topbar control that selects the active project the whole
 * UI is scoped to (workspace artifacts, RAG memory, knowledge base, workflow runs
 * are all partitioned per project on the backend). Switching sets the active
 * project (persisted; sent as X-Project-Id on every request) and invalidates the
 * query cache so every scoped view refetches. Supports inline create + a two-step
 * confirm before the irreversible hard-delete of a project's entire workspace.
 */
export function ProjectSwitcher({ className }: { className?: string }) {
  const qc = useQueryClient()
  const { data: projects = [] } = useProjects()
  const activeId = useProjectStore((s) => s.activeProjectId)
  const setActive = useProjectStore((s) => s.setActiveProject)
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()

  const [open, setOpen] = useState(false)
  const [confirmId, setConfirmId] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')

  const active = projects.find((p) => p.id === activeId)
  const activeName = active?.name ?? (activeId === DEFAULT_PROJECT_ID ? 'Default Workspace' : activeId)

  /** Re-fetch every project-scoped query so it reloads under the new X-Project-Id header. */
  const refetchScoped = () => void qc.invalidateQueries()

  function switchTo(id: string) {
    if (id !== activeId) {
      setActive(id)
      refetchScoped()
    }
    setOpen(false)
  }

  function confirmDelete(id: string) {
    // useDeleteProject handles the active-project fallback + scoped refetch.
    deleteProject.mutate(id, { onSuccess: () => setConfirmId(null) })
  }

  function submitCreate() {
    const trimmed = name.trim()
    if (!trimmed) return
    createProject.mutate(
      { name: trimmed },
      {
        onSuccess: (proj) => {
          setActive(proj.id)
          refetchScoped()
          setName('')
          setCreating(false)
          setOpen(false)
        },
      },
    )
  }

  function onOpenChange(next: boolean) {
    setOpen(next)
    if (!next) {
      setConfirmId(null)
      setCreating(false)
      setName('')
    }
  }

  return (
    <DropdownMenu open={open} onOpenChange={onOpenChange}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Switch project"
          className={cn(
            'focus-ring flex h-9 items-center gap-2 rounded-md bg-omnivra-surface-2 px-2.5 text-sm text-[#e4e4e7] transition-colors duration-200 hover:bg-omnivra-surface-3',
            className,
          )}
        >
          <FolderKanban className="h-4 w-4 text-omnivra-cyan" aria-hidden />
          <span className="max-w-[12rem] truncate font-medium">{activeName}</span>
          <ChevronsUpDown className="h-3.5 w-3.5 text-[#71717a]" aria-hidden />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="min-w-[17rem]">
        <DropdownMenuLabel>Projects</DropdownMenuLabel>
        <DropdownMenuSeparator />

        <div className="max-h-72 overflow-y-auto">
          {projects.map((p) =>
            confirmId === p.id ? (
              <div key={p.id} className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm">
                <span className="min-w-0 flex-1 truncate text-[#fafafa]">Delete “{p.name}”?</span>
                <button
                  type="button"
                  onClick={() => confirmDelete(p.id)}
                  disabled={deleteProject.isPending}
                  className="focus-ring inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold text-omnivra-red hover:bg-omnivra-red/10 disabled:opacity-50"
                >
                  {deleteProject.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Delete'}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmId(null)}
                  className="focus-ring rounded px-2 py-0.5 text-xs text-[#a1a1aa] hover:bg-white/[0.06]"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div key={p.id} className="group flex items-center gap-1 rounded-md pr-1 hover:bg-white/[0.06]">
                <button
                  type="button"
                  onClick={() => switchTo(p.id)}
                  className="focus-ring flex min-w-0 flex-1 items-center gap-2 rounded-md px-2 py-1.5 text-left"
                >
                  <Check
                    className={cn('h-4 w-4 shrink-0 text-omnivra-cyan', p.id === activeId ? 'opacity-100' : 'opacity-0')}
                    aria-hidden
                  />
                  <span className="min-w-0 flex-1 truncate text-[#e4e4e7]">{p.name}</span>
                  <span className="shrink-0 rounded bg-white/[0.06] px-1.5 text-[11px] tabular-nums text-[#a1a1aa]">
                    {p.taskCount}
                  </span>
                </button>
                {p.id !== DEFAULT_PROJECT_ID && (
                  <button
                    type="button"
                    aria-label={`Delete ${p.name}`}
                    onClick={() => setConfirmId(p.id)}
                    className="focus-ring rounded p-1 text-[#71717a] opacity-0 transition-opacity hover:bg-omnivra-red/10 hover:text-omnivra-red group-hover:opacity-100"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            ),
          )}
        </div>

        <DropdownMenuSeparator />

        {creating ? (
          <div className="flex items-center gap-1 px-1 py-1">
            <input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submitCreate()
                if (e.key === 'Escape') {
                  setCreating(false)
                  setName('')
                }
              }}
              placeholder="New project name…"
              className="focus-ring h-8 min-w-0 flex-1 rounded-md bg-omnivra-surface-2 px-2 text-sm text-[#e4e4e7] placeholder:text-[#71717a]"
            />
            <button
              type="button"
              onClick={submitCreate}
              disabled={!name.trim() || createProject.isPending}
              aria-label="Create project"
              className="focus-ring rounded p-1.5 text-omnivra-cyan hover:bg-omnivra-cyan/10 disabled:opacity-40"
            >
              {createProject.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            </button>
            <button
              type="button"
              onClick={() => {
                setCreating(false)
                setName('')
              }}
              aria-label="Cancel new project"
              className="focus-ring rounded p-1.5 text-[#a1a1aa] hover:bg-white/[0.06]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setCreating(true)}
            className="focus-ring flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-[#e4e4e7] hover:bg-white/[0.06]"
          >
            <FolderPlus className="h-4 w-4 text-omnivra-violet" aria-hidden />
            New project
          </button>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
