/**
 * Universal app runner API calls (cp-0054). Set up + run a WHOLE generated project (backend venv +
 * pip install + uvicorn, frontend npm install + vite) on local ports, poll live status/logs, stop it,
 * and download it as a zip. Uses the shared axios instance (X-Project-Id header via interceptor).
 */
import { api, apiUrl } from '@/lib/api/client'
import type { AppInfo, AppRunStatus } from '@/lib/api/types'

/** One card per generated app (workflow), de-duplicated across category dirs. GET /workspace/app/list. */
export async function listApps(): Promise<AppInfo[]> {
  const { data } = await api.get<AppInfo[]>('/workspace/app/list')
  return data
}

/** Start (or re-launch) a generated project's backend + frontend. POST /workspace/app/run. */
export async function runApp(dir: string): Promise<AppRunStatus> {
  const { data } = await api.post<AppRunStatus>('/workspace/app/run', { dir }, { timeout: 30_000 })
  return data
}

/** Live status + log tail for a project's targets. GET /workspace/app/status?dir=. */
export async function getAppStatus(dir: string): Promise<AppRunStatus> {
  const { data } = await api.get<AppRunStatus>('/workspace/app/status', { params: { dir } })
  return data
}

/** Stop a whole project (by dir) or one target (by runKey). POST /workspace/app/stop. */
export async function stopApp(body: { dir?: string; runKey?: string }): Promise<AppRunStatus> {
  const { data } = await api.post<AppRunStatus>('/workspace/app/stop', body, { timeout: 30_000 })
  return data
}

/**
 * Direct URL to download a generated project as a .zip (real app files only). Carries projectId as a
 * query param because an <a href download> doesn't send the X-Project-Id header the interceptor adds.
 */
export function appDownloadUrl(dir: string, projectId: string): string {
  return apiUrl(`/workspace/app/download?dir=${encodeURIComponent(dir)}&projectId=${encodeURIComponent(projectId)}`)
}
