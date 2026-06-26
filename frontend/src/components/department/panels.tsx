/**
 * Department command-center panels (cp-0048) — the shared building blocks every department
 * page composes: KPI strip, mini task board, recent workflows, activity feed, outputs gallery,
 * and provider usage. All driven by the GET /departments/{slug}/overview payload.
 */
import { Download, FileText, Inbox } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { Chip } from '@/components/ui/chip'
import { EmptyState } from '@/components/ui/empty-state'
import { IconTile } from '@/components/ui/icon-tile'
import { ProgressBar } from '@/components/ui/progress-bar'
import { StatCard } from '@/components/dashboard/stat-card'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import { resolveIcon } from '@/lib/api/icons'
import { documentUrl } from '@/lib/api/documents'
import { cn } from '@/lib/utils'
import type {
  Accent,
} from '@/types'
import type {
  DeptActivity,
  DeptOutput,
  DeptProviderCalls,
  DeptTask,
  DeptWorkflow,
  StatCardDTO,
} from '@/lib/api/types'

function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

/** KPI strip — the per-department metric tiles. */
export function DeptKpiStrip({ stats }: { stats: StatCardDTO[] }) {
  return (
    <Stagger className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
      {stats.map((s) => (
        <StaggerItem key={s.label}>
          <StatCard {...s} icon={resolveIcon(s.icon)} accent={s.accent as Accent} />
        </StaggerItem>
      ))}
    </Stagger>
  )
}

// --- mini task board --------------------------------------------------------
const TASK_COLUMNS: { key: string; label: string; tone: BadgeTone }[] = [
  { key: 'todo', label: 'To Do', tone: 'info' },
  { key: 'in_progress', label: 'In Progress', tone: 'warning' },
  { key: 'review', label: 'Review', tone: 'violet' },
  { key: 'done', label: 'Done', tone: 'success' },
]
const PRIORITY_ACCENT: Record<string, Accent> = { high: 'pink', medium: 'amber', low: 'cyan' }

export function DeptTaskBoard({ tasks }: { tasks: DeptTask[] }) {
  return (
    <GlassCard padding="md" className="flex flex-col gap-3">
      <SectionHeader label="Task Pipeline" count={tasks.length} />
      {tasks.length === 0 ? (
        <p className="py-6 text-center text-xs text-[#71717a]">No tasks assigned to this department yet.</p>
      ) : (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {TASK_COLUMNS.map((col) => {
            const items = tasks.filter((t) => t.status === col.key)
            return (
              <div key={col.key} className="flex flex-col gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] p-2.5">
                <div className="flex items-center justify-between">
                  <span className="section-label">{col.label}</span>
                  <NeonBadge tone={col.tone}>{items.length}</NeonBadge>
                </div>
                <div className="flex flex-col gap-1.5">
                  {items.slice(0, 6).map((t) => (
                    <div key={t.id} className="rounded-md border border-white/[0.06] bg-white/[0.02] px-2 py-1.5">
                      <p className="line-clamp-2 text-[11px] text-[#d4d4d8]">{t.title}</p>
                      <Chip label={t.priority} accent={PRIORITY_ACCENT[t.priority] ?? 'cyan'} className="mt-1" />
                    </div>
                  ))}
                  {items.length > 6 && <span className="text-[10px] text-[#71717a]">+{items.length - 6} more</span>}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </GlassCard>
  )
}

// --- recent workflows -------------------------------------------------------
const WF_TONE: Record<string, BadgeTone> = {
  completed: 'success',
  awaiting_approval: 'warning',
  running: 'info',
  failed: 'danger',
  stopped: 'danger',
  rolled_back: 'danger',
}

export function DeptWorkflows({ workflows }: { workflows: DeptWorkflow[] }) {
  return (
    <GlassCard padding="md" className="flex flex-col gap-3">
      <SectionHeader label="Recent Workflows" count={workflows.length} />
      {workflows.length === 0 ? (
        <p className="py-6 text-center text-xs text-[#71717a]">No workflow runs involving this department yet.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {workflows.map((w) => (
            <div key={w.id} className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
              <span className="min-w-0 flex-1 truncate text-xs text-[#d4d4d8]" title={w.task}>{w.task}</span>
              <span className="shrink-0 text-[10px] text-[#71717a]">{w.agents} agent{w.agents === 1 ? '' : 's'}</span>
              <NeonBadge tone={WF_TONE[w.status] ?? 'info'} dot className="shrink-0">{w.status.replace(/_/g, ' ')}</NeonBadge>
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  )
}

// --- activity feed ----------------------------------------------------------
export function DeptActivityFeed({ items }: { items: DeptActivity[] }) {
  return (
    <GlassCard padding="md" className="flex flex-col gap-3">
      <SectionHeader label="Live Activity" count={items.length} />
      {items.length === 0 ? (
        <p className="py-6 text-center text-xs text-[#71717a]">No recent activity.</p>
      ) : (
        <div className="flex flex-col gap-2.5">
          {items.map((a) => {
            const Icon = resolveIcon(a.icon)
            return (
              <div key={a.id} className="flex items-center gap-3">
                <IconTile accent={a.accent as Accent} size="sm" icon={Icon} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-medium text-[#e4e4e7]">{a.agent}</p>
                  <p className="truncate text-[11px] text-[#a1a1aa]">{a.action}</p>
                </div>
                <span className="shrink-0 text-[10px] text-[#71717a]">{a.time}</span>
              </div>
            )
          })}
        </div>
      )}
    </GlassCard>
  )
}

// --- outputs gallery --------------------------------------------------------
export function DeptOutputs({ outputs }: { outputs: DeptOutput[] }) {
  return (
    <GlassCard padding="md" className="flex flex-col gap-3">
      <SectionHeader label="Outputs" count={outputs.length} />
      {outputs.length === 0 ? (
        <EmptyState icon={Inbox} title="No outputs yet" hint="Files this department produces will appear here." className="py-8" />
      ) : (
        <div className="flex flex-col gap-1.5">
          {outputs.map((o) => {
            const fname = o.path.split('/').pop() ?? o.path
            return (
              <a
                key={`${o.projectId}|${o.path}`}
                href={documentUrl(o.path, o.projectId)}
                download
                className="focus-ring group flex items-center gap-2 rounded-md border border-white/[0.06] bg-white/[0.02] px-2.5 py-1.5 transition-colors hover:border-omnivra-cyan/40"
              >
                <FileText className="h-3.5 w-3.5 shrink-0 text-[#71717a]" aria-hidden />
                <span className="min-w-0 flex-1 truncate text-[11px] text-[#d4d4d8]" title={o.path}>{fname}</span>
                <Chip label={o.category} accent="blue" />
                <span className="shrink-0 text-[10px] text-[#71717a]">{fmtBytes(o.sizeBytes)}</span>
                <Download className="h-3.5 w-3.5 shrink-0 text-[#71717a] transition-colors group-hover:text-omnivra-cyan" aria-hidden />
              </a>
            )
          })}
        </div>
      )}
    </GlassCard>
  )
}

// --- provider usage ---------------------------------------------------------
export function DeptProviders({ usage }: { usage: DeptProviderCalls[] }) {
  const total = Math.max(1, usage.reduce((s, u) => s + u.calls, 0))
  return (
    <GlassCard padding="md" className="flex flex-col gap-3">
      <SectionHeader label="Provider Usage" />
      {usage.length === 0 ? (
        <p className="py-6 text-center text-xs text-[#71717a]">No provider calls recorded yet.</p>
      ) : (
        <div className="flex flex-col gap-2.5">
          {usage.map((u, i) => (
            <div key={u.provider} className={cn('flex flex-col gap-1')}>
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#d4d4d8]">{u.label}</span>
                <span className="tabular text-[#a1a1aa]">{u.calls}</span>
              </div>
              <ProgressBar value={Math.round((100 * u.calls) / total)} accent={(['cyan', 'violet', 'emerald', 'amber', 'pink'][i % 5]) as Accent} />
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  )
}
