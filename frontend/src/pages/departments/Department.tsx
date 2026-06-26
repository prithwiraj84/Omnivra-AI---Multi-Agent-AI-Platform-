import { useParams } from 'react-router-dom'
import { Users } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { EmptyState } from '@/components/ui/empty-state'
import { NeonBadge } from '@/components/ui/neon-badge'
import { Reveal } from '@/components/common/reveal'
import { TaskExecutionChart } from '@/components/dashboard/task-execution-chart'
import type { AreaChartSeries } from '@/components/ui/charts/area-chart'
import { DeptAgentGrid } from '@/components/department/agent'
import {
  DeptActivityFeed,
  DeptKpiStrip,
  DeptOutputs,
  DeptProviders,
  DeptTaskBoard,
  DeptWorkflows,
} from '@/components/department/panels'
import { DeptQuickAction, DeptTailoredPanel } from '@/components/department/actions'
import { useDepartmentOverview } from '@/hooks/useDepartmentOverview'
import { AGENTS } from '@/config/agents'
import type { Accent } from '@/types'
import type { DeptAgent } from '@/lib/api/types'

/** Local header metadata + roster mapping, so the page renders instantly before the
 *  live overview loads (and still works if the backend is down). Mirrors the backend. */
interface DeptMeta {
  title: string
  note: string
  accent: Accent
  departments: string[]
}
const DEPT_META: Record<string, DeptMeta> = {
  executive: { title: 'Executive', accent: 'cyan', departments: ['Executive'], note: 'Strategic direction and delegation. The CEO / Manager plans the roadmap and routes work to the right department.' },
  architecture: { title: 'Architecture', accent: 'violet', departments: ['Architecture', 'Design'], note: 'System design and user experience. Architects and designers shape how each build comes together.' },
  engineering: { title: 'Engineering', accent: 'blue', departments: ['Engineering'], note: 'The builders. Database, frontend, backend and API engineers turn plans into working software.' },
  quality: { title: 'Quality & Security', accent: 'emerald', departments: ['Quality & Security'], note: 'Verification and hardening. QA and SecOps test every build and scan it for vulnerabilities.' },
  marketing: { title: 'Marketing', accent: 'amber', departments: ['Marketing'], note: 'Reach and growth. SEO, social and reel-automation agents take the product to its audience.' },
  documentation: { title: 'Documentation', accent: 'violet', departments: ['Documentation'], note: 'Knowledge capture. Documentation and presentation agents keep the company explainable.' },
  'system-ops': { title: 'System Operations', accent: 'cyan', departments: ['System Ops'], note: 'The control plane. Classification, routing, memory, notification and log-analysis utilities keep the OS running.' },
}

const EXECUTION_SERIES: AreaChartSeries[] = [
  { key: 'completed', label: 'Completed', color: '#10b981' },
  { key: 'inProgress', label: 'In Progress', color: '#3b82f6' },
  { key: 'failed', label: 'Failed', color: '#ef4444' },
]

export interface DepartmentProps {
  title?: string
  slug?: string
}

/**
 * Department — the per-department COMMAND CENTER. Resolves the route slug to a department,
 * loads its live overview (agents+status, KPIs, tasks, runs, activity, outputs, usage), and
 * composes the shared panels + a per-department tailored panel + a quick-action launcher.
 * Renders instantly from a static roster fallback, then upgrades to live data.
 */
export function Department({ slug: slugProp }: DepartmentProps = {}) {
  const params = useParams<{ slug: string }>()
  const slug = slugProp ?? params.slug ?? ''
  const meta = DEPT_META[slug]
  const { data } = useDepartmentOverview(meta ? slug : '')

  if (!meta) {
    return (
      <GlassCard padding="none" className="overflow-hidden">
        <EmptyState icon={Users} title="Unknown department" hint="Pick a department from the sidebar." className="py-16" />
      </GlassCard>
    )
  }

  const title = data?.title ?? meta.title
  const note = data?.note ?? meta.note
  const accent = (data?.accent as Accent) ?? meta.accent

  // Instant static agents (idle) until the live overview arrives.
  const fallbackAgents: DeptAgent[] = AGENTS.filter((a) => meta.departments.includes(a.department)).map((a) => ({
    id: a.id, name: a.name, status: 'idle', provider: a.provider, model: a.model,
    modelLabel: a.modelLabel, accent: meta.accent, kind: a.kind, calls: 0, lastActivity: null, responsibilities: [],
  }))
  const agents = data?.agents?.length ? data.agents : fallbackAgents

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <GlassCard padding="md" glow={accent} className="flex flex-col gap-3">
          <SectionHeader label={title} count={agents.length} action={<NeonBadge tone="cyan">Department</NeonBadge>} />
          <p className="max-w-prose text-sm leading-relaxed text-[#a1a1aa]">{note}</p>
        </GlassCard>
      </Reveal>

      {data && <DeptKpiStrip stats={data.stats} />}

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        {/* Main column */}
        <div className="flex min-w-0 flex-col gap-5">
          <GlassCard padding="md" className="flex flex-col gap-3">
            <SectionHeader label="Agents" count={agents.length} />
            <DeptAgentGrid agents={agents} />
          </GlassCard>

          <DeptTaskBoard tasks={data?.tasks ?? []} />

          <div className="grid gap-5 lg:grid-cols-2">
            <DeptWorkflows workflows={data?.workflows ?? []} />
            <DeptActivityFeed items={data?.activity ?? []} />
          </div>

          <DeptOutputs outputs={data?.outputs ?? []} />

          {data && data.execution.length > 0 && (
            <TaskExecutionChart data={data.execution} series={EXECUTION_SERIES} />
          )}
        </div>

        {/* Side column */}
        <div className="flex flex-col gap-5">
          <DeptQuickAction slug={slug} title={title} />
          <DeptTailoredPanel slug={slug} />
          <DeptProviders usage={data?.providerUsage ?? []} />
        </div>
      </div>
    </div>
  )
}
