/**
 * Task hooks (Phase 10).
 *  - useTasks(projectId?): the live task list, optionally scoped to one project.
 *    The query key carries the projectId so switching scope refetches cleanly.
 *  - useCreateTask() / useUpdateTask() / useDeleteTask(): mutations that invalidate
 *    both ["tasks"] (the board) and ["projects"] (the per-project taskCount).
 * Queries fail gracefully offline (jsdom/tests) — consumers default to [] on no data.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createTask, deleteTask, listTasks, updateTask } from '@/lib/api/projects'
import type { Task, TaskCreate } from '@/lib/api/types'

/** Live task list, optionally scoped to one project — one retry so offline settles fast. */
export function useTasks(projectId?: string) {
  return useQuery<Task[]>({
    queryKey: ['tasks', projectId],
    queryFn: () => listTasks(projectId ? { projectId } : undefined),
    retry: 1,
  })
}

/** Create a task; refreshes the board + per-project counts on success. */
export function useCreateTask() {
  const qc = useQueryClient()
  return useMutation<Task, Error, TaskCreate>({
    mutationFn: (body) => createTask(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

interface UpdateTaskVars {
  id: string
  patch: { status?: string; title?: string; priority?: string }
}

/** Patch a task (status/title/priority); refreshes the board + counts on success. */
export function useUpdateTask() {
  const qc = useQueryClient()
  return useMutation<Task, Error, UpdateTaskVars>({
    mutationFn: ({ id, patch }) => updateTask(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

/** Delete a task; refreshes the board + per-project counts on success. */
export function useDeleteTask() {
  const qc = useQueryClient()
  return useMutation<{ ok: boolean }, Error, string>({
    mutationFn: (id) => deleteTask(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}
