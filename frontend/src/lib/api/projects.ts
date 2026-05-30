/**
 * Projects + Tasks API calls (Phase 10). Uses the shared `@/lib/api/client`
 * axios instance (baseURL '/api'). Projects are the company's workstreams;
 * tasks are the units of work, optionally attached to a project and/or an agent.
 * Mutations require auth only when AUTH_ENABLED (open in dev/tests).
 */
import { api } from '@/lib/api/client'
import type { Project, ProjectCreate, Task, TaskCreate } from '@/lib/api/types'

// --- Projects --------------------------------------------------------------

/** Every project, each with its derived `taskCount`. GET /projects. */
export async function listProjects(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/projects')
  return data
}

/** Create a new project. POST /projects. */
export async function createProject(body: ProjectCreate): Promise<Project> {
  const { data } = await api.post<Project>('/projects', body)
  return data
}

/** Delete a project (and its tasks). DELETE /projects/{id}. */
export async function deleteProject(id: string): Promise<{ ok: boolean }> {
  const { data } = await api.delete<{ ok: boolean }>(`/projects/${id}`)
  return data
}

// --- Tasks -----------------------------------------------------------------

/** List tasks, optionally filtered by projectId and/or status. GET /tasks. */
export async function listTasks(params?: {
  projectId?: string
  status?: string
}): Promise<Task[]> {
  const { data } = await api.get<Task[]>('/tasks', { params })
  return data
}

/** Create a new task (created with status "todo"). POST /tasks. */
export async function createTask(body: TaskCreate): Promise<Task> {
  const { data } = await api.post<Task>('/tasks', body)
  return data
}

/** Patch a task's title/status/priority. PATCH /tasks/{id}. */
export async function updateTask(
  id: string,
  patch: { status?: string; title?: string; priority?: string },
): Promise<Task> {
  const { data } = await api.patch<Task>(`/tasks/${id}`, patch)
  return data
}

/** Delete a task. DELETE /tasks/{id}. */
export async function deleteTask(id: string): Promise<{ ok: boolean }> {
  const { data } = await api.delete<{ ok: boolean }>(`/tasks/${id}`)
  return data
}
