/**
 * Universal app runner hooks (cp-0054).
 *  - useAppStatus(dir): live status for a generated project; polls fast (2s) while a target is
 *    installing/starting, slow (8s) while running, and stops when everything is idle/terminal.
 *  - useRunApp(): start the project's backend + frontend.
 *  - useStopApp(): stop the whole project or one target.
 * All scoped to the active project via the X-Project-Id header.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getAppStatus, listApps, runApp, stopApp } from '@/lib/api/appRunner'
import type { AppInfo, AppRunStatus } from '@/lib/api/types'
import { useProjectStore } from '@/store/project'

const ACTIVE = new Set(['installing', 'starting'])

/** One entry per generated app (workflow), de-duplicated to its best root. Polls every 15s. */
export function useApps() {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<AppInfo[]>({
    queryKey: ['apps', projectId],
    queryFn: listApps,
    refetchInterval: 15_000,
    retry: 1,
  })
}

/** Poll a project's run status. `enabled=false` skips polling (e.g. when no app is selected). */
export function useAppStatus(dir: string | null, enabled = true) {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<AppRunStatus>({
    queryKey: ['appStatus', projectId, dir],
    queryFn: () => getAppStatus(dir as string),
    enabled: enabled && !!dir,
    refetchInterval: (query) => {
      const t = query.state.data?.targets ?? []
      if (t.some((x) => ACTIVE.has(x.status))) return 2_000 // setting up / starting -> poll fast
      if (t.some((x) => x.status === 'running')) return 8_000 // running -> keep an eye on it
      return false // idle / stopped / error -> stop polling
    },
    retry: 1,
  })
}

/** Start (or re-launch) a project's backend + frontend; primes the status cache on success. */
export function useRunApp() {
  const qc = useQueryClient()
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useMutation<AppRunStatus, Error, string>({
    mutationFn: (dir) => runApp(dir),
    onSuccess: (data, dir) => {
      qc.setQueryData(['appStatus', projectId, dir], data)
      qc.invalidateQueries({ queryKey: ['appStatus', projectId, dir] })
    },
  })
}

/** Stop a whole project (by dir) or one target (by runKey); refreshes the status. */
export function useStopApp(dir: string) {
  const qc = useQueryClient()
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useMutation<AppRunStatus, Error, { dir?: string; runKey?: string }>({
    mutationFn: (body) => stopApp(body),
    onSuccess: (data) => {
      qc.setQueryData(['appStatus', projectId, dir], data)
      qc.invalidateQueries({ queryKey: ['appStatus', projectId, dir] })
    },
  })
}
