/**
 * Project hooks (Phase 10).
 *  - useProjects(): the live project list (each with its derived taskCount).
 *  - useCreateProject() / useDeleteProject(): mutations that invalidate ["projects"]
 *    so the list + counts refresh on success.
 * Queries fail gracefully offline (jsdom/tests) — consumers default to [] on no data.
 */
import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createProject, deleteProject, listProjects } from '@/lib/api/projects'
import type { Project, ProjectCreate } from '@/lib/api/types'
import { DEFAULT_PROJECT_ID, useProjectStore } from '@/store/project'

/**
 * True when the persisted active project no longer exists server-side. The default id is never
 * stale — the backend maps it to this user's Default Workspace on every request. Exported for
 * tests.
 */
export function isStaleProject(activeProjectId: string, projects: Project[]): boolean {
  if (activeProjectId === DEFAULT_PROJECT_ID) return false
  return !projects.some((p) => p.id === activeProjectId)
}

/** Live project list — one retry so an offline host settles quickly.
 *
 * SELF-HEALS a stale active project: the id is persisted in localStorage, but the project
 * behind it can vanish server-side (a hosted backend's ephemeral disk resets on restart, or
 * per-user mode hides projects created before sign-in). Every request then carries a dead
 * X-Project-Id and 404s — "Assign to CEO", social drafts, tasks, all of it — until the user
 * happens to switch projects by hand. When the loaded list doesn't contain the active id,
 * fall back to the Default Workspace and refetch every scoped view.
 */
export function useProjects() {
  const qc = useQueryClient()
  const query = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: listProjects,
    retry: 1,
  })

  const { data } = query
  useEffect(() => {
    if (!data) return // never reset on a failed/pending fetch — offline is not "stale"
    const { activeProjectId, setActiveProject } = useProjectStore.getState()
    if (isStaleProject(activeProjectId, data)) {
      setActiveProject(DEFAULT_PROJECT_ID)
      void qc.invalidateQueries() // every project-scoped view was querying a dead project
    }
  }, [data, qc])

  return query
}

/** Create a project; refreshes the project list on success. */
export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation<Project, Error, ProjectCreate>({
    mutationFn: (body) => createProject(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

/**
 * Delete a project (hard-deletes its entire workspace on the backend). Refreshes
 * the project list + tasks, and — if the deleted project was the active one —
 * falls back to the Default Workspace and refetches every project-scoped view.
 */
export function useDeleteProject() {
  const qc = useQueryClient()
  return useMutation<{ ok: boolean }, Error, string>({
    mutationFn: (id) => deleteProject(id),
    onSuccess: (_data, id) => {
      const { activeProjectId, setActiveProject } = useProjectStore.getState()
      if (id === activeProjectId) {
        setActiveProject(DEFAULT_PROJECT_ID)
        void qc.invalidateQueries() // we switched projects — refetch all scoped views
      } else {
        qc.invalidateQueries({ queryKey: ['projects'] })
        qc.invalidateQueries({ queryKey: ['tasks'] })
      }
    },
  })
}
