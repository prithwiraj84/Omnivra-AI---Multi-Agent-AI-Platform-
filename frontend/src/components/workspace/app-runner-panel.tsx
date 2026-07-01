/**
 * AppRunnerPanel (cp-0054) — "Run" a WHOLE generated project, not just one file. For each generated
 * app (a docs/wf_* project), one button sets up a per-app venv + installs deps + launches the backend
 * (uvicorn) and frontend (vite) on local ports — so it runs without the "ModuleNotFoundError" the
 * single-file runner hit. Plus live status + logs, a real Stop, and Download-as-ZIP (app files only).
 */
import { useEffect, useRef, useState } from 'react'
import {
  Box,
  Download,
  ExternalLink,
  FileCode,
  Loader2,
  Play,
  Server,
  Square,
  Terminal,
} from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { EmptyState } from '@/components/ui/empty-state'
import { Button } from '@/components/ui/button'
import { useApps, useAppStatus, useRunApp, useStopApp } from '@/hooks/useAppRunner'
import { appDownloadUrl } from '@/lib/api/appRunner'
import { useProjectStore } from '@/store/project'
import type { AppTarget, AppTargetStatus } from '@/lib/api/types'

const STATUS_VIEW: Record<AppTargetStatus, { tone: BadgeTone; label: string; busy?: boolean }> = {
  idle: { tone: 'info', label: 'Idle' },
  installing: { tone: 'warning', label: 'Installing…', busy: true },
  starting: { tone: 'warning', label: 'Starting…', busy: true },
  running: { tone: 'success', label: 'Running' },
  exited: { tone: 'danger', label: 'Exited' },
  error: { tone: 'danger', label: 'Error' },
  stopped: { tone: 'info', label: 'Stopped' },
}

function TargetRow({ t, dir }: { t: AppTarget; dir: string }) {
  const stop = useStopApp(dir)
  const view = STATUS_VIEW[t.status] ?? STATUS_VIEW.idle
  const Icon = t.kind === 'python' ? Server : FileCode
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md border border-white/[0.06] bg-white/[0.02] px-2.5 py-2">
      <Icon className="h-4 w-4 shrink-0 text-omnivra-cyan" aria-hidden />
      <span className="text-sm font-medium text-[#e4e4e7]">{t.name}</span>
      <span className="text-[10px] uppercase tracking-wide text-[#71717a]">{t.framework || t.kind}</span>
      <NeonBadge tone={view.tone} dot>
        {view.busy && <Loader2 className="h-3 w-3 animate-spin" aria-hidden />}
        {view.label}
      </NeonBadge>
      <div className="ml-auto flex items-center gap-2">
        {t.status === 'running' && t.url && (
          <a
            href={t.url}
            target="_blank"
            rel="noreferrer"
            className="focus-ring inline-flex items-center gap-1 rounded-md border border-omnivra-emerald/30 px-2 py-1 text-xs font-medium text-omnivra-emerald transition-colors hover:bg-omnivra-emerald/10"
          >
            <ExternalLink className="h-3.5 w-3.5" aria-hidden />
            Open {t.port ? `:${t.port}` : ''}
          </a>
        )}
        {(t.status === 'running' || t.status === 'starting' || t.status === 'installing') && (
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={stop.isPending}
            onClick={() => stop.mutate({ runKey: t.runKey })}
            className="hover:text-omnivra-red"
          >
            <Square className="h-3.5 w-3.5" aria-hidden />
            Stop
          </Button>
        )}
      </div>
      {t.note && t.status !== 'running' && (
        <p className="w-full text-[11px] text-[#a1a1aa]">{t.note}</p>
      )}
    </div>
  )
}

function AppRunnerCard({ dir, name }: { dir: string; name: string }) {
  const projectId = useProjectStore((s) => s.activeProjectId)
  const { data } = useAppStatus(dir)
  const run = useRunApp()
  const stop = useStopApp(dir)
  const [showLogs, setShowLogs] = useState(false)
  const logRef = useRef<HTMLDivElement>(null)

  const targets = data?.targets ?? []
  const anyActive = targets.some((t) => ['installing', 'starting', 'running'].includes(t.status))
  const setting = targets.some((t) => ['installing', 'starting'].includes(t.status)) || run.isPending
  const logs = targets
    .map((t) => (t.logsTail ? `=== ${t.name} (${t.kind}) ===\n${t.logsTail}` : ''))
    .filter(Boolean)
    .join('\n\n')
  // Auto-open logs while it's installing/starting so progress (and any error) is visible immediately.
  const logsOpen = showLogs || setting

  // Keep the log view pinned to the newest lines — the reason a target exited is at the BOTTOM.
  useEffect(() => {
    if (logsOpen && logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [logs, logsOpen])

  return (
    <GlassCard className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <Box className="h-4 w-4 shrink-0 text-omnivra-amber" aria-hidden />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-[#fafafa]">{name}</p>
          <p className="truncate font-mono text-[10px] text-[#71717a]">{dir}</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Button
            type="button"
            size="sm"
            disabled={setting}
            onClick={() => run.mutate(dir)}
            title="Set up deps + run the backend & frontend"
          >
            {setting ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Play className="h-3.5 w-3.5" aria-hidden />}
            {anyActive ? 'Re-run' : 'Run'}
          </Button>
          {anyActive && (
            <Button type="button" size="sm" variant="outline" disabled={stop.isPending} onClick={() => stop.mutate({ dir })} className="hover:text-omnivra-red">
              <Square className="h-3.5 w-3.5" aria-hidden />
              Stop all
            </Button>
          )}
          <a
            href={appDownloadUrl(dir, projectId)}
            download
            className="focus-ring inline-flex items-center gap-1.5 rounded-md border border-white/10 px-2.5 py-1.5 text-xs font-medium text-[#d4d4d8] transition-colors hover:border-omnivra-cyan/40 hover:text-omnivra-cyan"
          >
            <Download className="h-3.5 w-3.5" aria-hidden />
            ZIP
          </a>
        </div>
      </div>

      {targets.length > 0 ? (
        <div className="flex flex-col gap-1.5">
          {targets.map((t) => (
            <TargetRow key={t.runKey} t={t} dir={dir} />
          ))}
        </div>
      ) : (
        <p className="text-xs text-[#71717a]">{data?.note || 'No runnable backend/frontend detected here.'}</p>
      )}

      {logs && (
        <div className="rounded-md border border-white/[0.08] bg-black/30">
          <button
            type="button"
            onClick={() => setShowLogs((s) => !s)}
            aria-expanded={showLogs}
            className="focus-ring flex w-full items-center gap-2 px-3 py-2 text-[11px] font-medium text-[#d4d4d8]"
          >
            <Terminal className="h-3.5 w-3.5 text-omnivra-cyan" aria-hidden />
            {logsOpen ? 'Hide' : 'Show'} logs
          </button>
          {logsOpen && (
            <div ref={logRef} className="max-h-[20rem] overflow-auto">
              <pre className="whitespace-pre-wrap break-words px-3 pb-3 font-mono text-[11px] leading-relaxed text-[#a1a1aa]">
                {logs}
              </pre>
            </div>
          )}
        </div>
      )}
    </GlassCard>
  )
}

/**
 * AppRunnerPanel — one card per generated app (workflow), de-duplicated across the workspace category
 * dirs to its best root. One-click Run (venv + deps + backend & frontend), live status/logs, Stop, ZIP.
 */
export function AppRunnerPanel() {
  const { data: apps } = useApps()
  const list = apps ?? []

  return (
    <GlassCard padding="none" className="overflow-hidden">
      <div className="border-b border-white/5 p-5">
        <SectionHeader label="Generated Apps" count={list.length} />
      </div>
      {list.length === 0 ? (
        <EmptyState
          icon={Box}
          title="No runnable apps yet"
          hint="When the CEO builds an app (backend + frontend), it appears here with a one-click Run that installs its dependencies and serves it locally."
          className="py-12"
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 p-4 xl:grid-cols-2">
          {list.map((a) => (
            <AppRunnerCard key={a.wfId} dir={a.dir} name={a.name} />
          ))}
        </div>
      )}
    </GlassCard>
  )
}
