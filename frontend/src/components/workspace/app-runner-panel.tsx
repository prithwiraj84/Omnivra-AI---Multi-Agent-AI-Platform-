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
import { useSystemInfo } from '@/hooks/useSystem'
import { appDownloadUrl, appPreviewUrl } from '@/lib/api/appRunner'
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

/** Statuses a target can no longer leave on its own — nothing more is coming. */
const TERMINAL: AppTargetStatus[] = ['exited', 'error', 'stopped']

/**
 * What a Run click should do on this deployment. Exported for tests.
 *  - 'launch'  the runner can start real servers (local) — open the placeholder tab + POST run
 *  - 'preview' launching is off but the app can render in the browser — open the preview
 *  - 'explain' launching is off and there is nothing browser-runnable (backend-only app):
 *              opening a tab would only ever show a dead end, so say so INLINE instead.
 */
export function runAction(runnerOff: boolean, previewHref: string | null): 'launch' | 'preview' | 'explain' {
  if (!runnerOff) return 'launch'
  return previewHref ? 'preview' : 'explain'
}

/**
 * The target the "Run" tab should land on: the FRONTEND if the app has one, because "run the
 * app" means the website, not the API root it talks to. Falls back to whatever is serving
 * (a backend-only project opens its own root). Exported for tests.
 */
export function openableTarget(targets: AppTarget[]): AppTarget | undefined {
  const live = targets.filter((t) => t.status === 'running' && !!t.url)
  return live.find((t) => t.kind === 'node') ?? live[0]
}

/**
 * True when nothing is serving and nothing is still working towards it, so a tab waiting on
 * this app will never get a URL. 'idle' is deliberately NOT terminal — it is also the state
 * before the run request has been answered, and treating it as terminal would abandon the tab
 * a few milliseconds after the click. Exported for tests.
 */
export function runSettled(targets: AppTarget[]): boolean {
  return targets.length > 0 && targets.every((t) => TERMINAL.includes(t.status))
}

/** The placeholder document shown in the new tab while the app boots. */
function bootingDoc(appName: string): string {
  const safe = appName.replace(/[<>&]/g, '')
  return `<!doctype html><html><head><meta charset="utf-8"/><title>Starting ${safe}…</title>
<style>
 :root{color-scheme:dark}
 body{margin:0;min-height:100vh;display:grid;place-items:center;background:#09090b;
      color:#e4e4e7;font:400 14px/1.6 ui-sans-serif,system-ui,-apple-system,sans-serif}
 .w{text-align:center;padding:2rem;max-width:34rem}
 .s{width:34px;height:34px;margin:0 auto 1.25rem;border-radius:50%;
    border:2px solid rgba(255,255,255,.12);border-top-color:#22d3ee;animation:r .8s linear infinite}
 @keyframes r{to{transform:rotate(360deg)}}
 h1{margin:0 0 .5rem;font-size:1rem;font-weight:600;color:#fafafa}
 p{margin:0;color:#a1a1aa;font-size:13px}
</style></head><body><div class="w">
 <div class="s"></div>
 <h1>Starting ${safe}…</h1>
 <p id="msg">Installing dependencies and launching the server. This tab opens the app automatically.</p>
</div></body></html>`
}

function AppRunnerCard({ dir, name, previewPath }: { dir: string; name: string; previewPath?: string | null }) {
  const projectId = useProjectStore((s) => s.activeProjectId)
  const { data } = useAppStatus(dir)
  const { data: sysInfo } = useSystemInfo()
  const run = useRunApp()
  const stop = useStopApp(dir)
  const [showLogs, setShowLogs] = useState(false)
  const [popupBlocked, setPopupBlocked] = useState(false)
  const [cannotRun, setCannotRun] = useState(false)
  const logRef = useRef<HTMLDivElement>(null)
  // The tab opened by the Run click, waiting to be pointed at the app once it is serving.
  const pendingTab = useRef<Window | null>(null)

  const targets = data?.targets ?? []
  // Shared hosts (HF Space) disable the LAUNCH runner — a launched app's port isn't reachable
  // there. Serving the app's files still is, so Run becomes a static Preview instead of a dead
  // end. Only an explicit false counts: while /system/info is loading we assume launching works.
  const runnerOff = sysInfo?.appRunnerEnabled === false
  const preview = data?.previewPath ?? previewPath ?? null
  const previewHref = preview ? appPreviewUrl(preview, projectId) : null
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

  /** Replace the placeholder tab's message when the app isn't going to come up. */
  const tellTab = (message: string) => {
    const win = pendingTab.current
    if (!win || win.closed) return
    try {
      const el = win.document.getElementById('msg')
      if (el) el.textContent = message
      const spinner = win.document.querySelector('.s') as HTMLElement | null
      if (spinner) spinner.style.animation = 'none'
    } catch {
      /* the tab navigated away or was closed — nothing to update */
    }
  }

  // Send the tab opened on click to the app as soon as a target is actually serving. This is why
  // the window is opened in the click handler and merely REDIRECTED here: window.open() from an
  // async callback (the status poll) is not a user gesture, so browsers block it as a popup.
  useEffect(() => {
    const win = pendingTab.current
    if (!win) return
    if (win.closed) {
      pendingTab.current = null
      return
    }
    const target = openableTarget(targets)
    if (target?.url) {
      win.location.replace(target.url)
      pendingTab.current = null
      return
    }
    // No live server is coming on this deployment — the static preview IS the destination.
    if (runnerOff && previewHref) {
      win.location.replace(previewHref)
      pendingTab.current = null
      return
    }
    if (run.isPending) return
    if (runSettled(targets)) {
      tellTab('The app stopped before it started serving. Check the logs in Omnivra → Workspace.')
      pendingTab.current = null
    } else if (targets.length === 0 && data?.note) {
      tellTab(data.note)
      pendingTab.current = null
    }
  }, [targets, run.isPending, data?.note, runnerOff, previewHref])

  const onRun = () => {
    const action = runAction(runnerOff, previewHref)
    if (action === 'preview') {
      window.open(previewHref as string, '_blank', 'noopener')
      return
    }
    if (action === 'explain') {
      // Backend-only app on a host that can't launch servers: a tab would only show a dead
      // end (the reported "about:blank" + disabled note). Explain inline instead.
      setCannotRun(true)
      return
    }
    // Open the tab HERE, synchronously inside the click, so it counts as a user gesture.
    if (!pendingTab.current || pendingTab.current.closed) {
      const win = window.open('', '_blank')
      if (win) {
        try {
          win.document.write(bootingDoc(name))
          win.document.close()
        } catch {
          /* a hardened browser may refuse the write; the redirect below still works */
        }
        pendingTab.current = win
        setPopupBlocked(false)
      } else {
        // Blocked: don't fail the run — it still starts, and the Open link appears when ready.
        setPopupBlocked(true)
      }
    }
    run.mutate(dir)
  }

  return (
    <GlassCard className="flex h-full flex-col gap-3">
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
            onClick={onRun}
            title="Set up deps, run the backend & frontend, and open the app in a new tab"
          >
            {setting ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : runnerOff && previewHref ? <ExternalLink className="h-3.5 w-3.5" aria-hidden /> : <Play className="h-3.5 w-3.5" aria-hidden />}
            {runnerOff && previewHref ? 'Preview' : anyActive ? 'Re-run' : 'Run'}
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
        <p className="flex flex-1 items-center justify-center text-xs text-[#71717a]">{data?.note || 'No runnable backend/frontend detected here.'}</p>
      )}

      {cannotRun && (
        <p className="text-[11px] text-omnivra-amber" role="status">
          This deployment can’t launch servers, and this app has no browser-runnable frontend
          (it’s backend-only) — use ZIP above and run it locally with the included README.
        </p>
      )}

      {popupBlocked && (
        <p className="text-[11px] text-omnivra-amber" role="status">
          Your browser blocked the new tab. The app is still starting — use the Open button above when
          it turns green, or allow pop-ups for this site to have it open automatically.
        </p>
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
            <AppRunnerCard key={a.wfId} dir={a.dir} name={a.name} previewPath={a.previewPath} />
          ))}
        </div>
      )}
    </GlassCard>
  )
}
