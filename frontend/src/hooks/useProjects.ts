/**
 * Project hooks (Phase 10).
 *  - useProjects(): the live project list (each with its derived taskCount).
 *  - useCreateProject() / useDeleteProject(): mutations that invalidate ["projects"]
 *    so the list + counts refresh on success.
 * Queries fail gracefully offline (jsdom/tests) — consumers default to [] on no data.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createProject, deleteProject, listProjects } from '@/lib/api/projects'
import type { Project, ProjectCreate } from '@/lib/api/types'
import { DEFAULT_PROJECT_ID, useProjectStore } from '@/store/project'

/** Live project list — one retry so an offline host settles quickly. */
export function useProjects() {
  return useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: listProjects,
    retry: 1,
  })
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
