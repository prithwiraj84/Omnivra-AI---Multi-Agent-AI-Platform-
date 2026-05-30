import { useState, type FormEvent } from 'react'
import { FolderGit2, ListChecks, Plus, Trash2 } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { Chip } from '@/components/ui/chip'
import { IconTile } from '@/components/ui/icon-tile'
import { IconButton } from '@/components/ui/icon-button'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { useCreateProject, useDeleteProject, useProjects } from '@/hooks/useProjects'
import type { Project } from '@/lib/api/types'

/** Map a project lifecycle status to a NeonBadge tone. */
function statusTone(status: string): BadgeTone {
  switch (status) {
    case 'active':
      return 'success'
    case 'paused':
      return 'warning'
    case 'archived':
      return 'info'
    default:
      return 'cyan'
  }
}

/** One project card: name, description, a status NeonBadge, a taskCount chip + a delete control. */
function ProjectCard({ project, onDelete, deleting }: {
  project: Project
  onDelete: (id: string) => void
  deleting: boolean
}) {
  return (
    <GlassCard interactive glow="violet" className="flex h-full flex-col gap-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <IconTile accent="violet" icon={FolderGit2} />
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold text-[#fafafa]">{project.name}</h3>
            <NeonBadge tone={statusTone(project.status)} dot className="mt-1.5">
              {project.status}
            </NeonBadge>
          </div>
        </div>
        <IconButton
          icon={Trash2}
          aria-label={`Delete project ${project.name}`}
          onClick={() => onDelete(project.id)}
          disabled={deleting}
          className="hover:text-omnivra-red"
        />
      </div>

      {project.description && (
        <p className="line-clamp-3 text-xs leading-relaxed text-[#a1a1aa]">{project.description}</p>
      )}

      <div className="mt-auto flex items-center gap-2 pt-1">
        <Chip
          label={`${project.taskCount} task${project.taskCount === 1 ? '' : 's'}`}
          icon={ListChecks}
          accent="violet"
        />
      </div>
    </GlassCard>
  )
}

/**
 * Projects — the workstream browser. A "Projects" SectionHeader (+ live count), a
 * compact create form (name input + "New Project" → useCreateProject), and a
 * staggered grid of interactive project GlassCards. Each card shows the name, a
 * status NeonBadge, the description and a taskCount chip, with a per-card delete
 * (trash) IconButton (useDeleteProject). Offline (jsdom/tests) the query never
 * resolves and the EmptyState renders.
 */
export function Projects() {
  const [name, setName] = useState('')
  const { data: projects, isError } = useProjects()
  const create = useCreateProject()
  const remove = useDeleteProject()

  const list = projects ?? []

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed || create.isPending) return
    create.mutate({ name: trimmed }, { onSuccess: () => setName('') })
  }

  return (
    <div className="flex flex-col gap-5">
      <GlassCard padding="none" className="overflow-hidden">
        <div className="flex flex-col gap-4 p-5">
          <SectionHeader label="Projects" count={list.length} />

          <form onSubmit={submit} className="flex max-w-xl items-center gap-2">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="New project name…"
              aria-label="New project name"
              className="focus-ring h-9 flex-1 rounded-md bg-omnivra-surface-2 px-3 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
            />
            <Button type="submit" size="sm" disabled={create.isPending || name.trim().length === 0}>
              <Plus aria-hidden />
              {create.isPending ? 'Creating…' : 'New Project'}
            </Button>
          </form>

          {create.isError && (
            <p className="text-xs text-omnivra-pink" role="status" aria-live="polite">
              Could not create the project. Try again.
            </p>
          )}
        </div>
      </GlassCard>

      {list.length === 0 ? (
        <Reveal>
          <GlassCard padding="lg">
            <EmptyState
              icon={FolderGit2}
              title={isError ? 'Could not load projects' : 'No projects yet'}
              hint={
                isError
                  ? 'The company could not be reached. Check the backend and try again.'
                  : 'Create your first project above to start organizing the company’s work.'
              }
              className="py-12"
            />
          </GlassCard>
        </Reveal>
      ) : (
        <Stagger className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {list.map((project) => (
            <StaggerItem key={project.id}>
              <ProjectCard
                project={project}
                onDelete={(id) => remove.mutate(id)}
                deleting={remove.isPending && remove.variables === project.id}
              />
            </StaggerItem>
          ))}
        </Stagger>
      )}
    </div>
  )
}
