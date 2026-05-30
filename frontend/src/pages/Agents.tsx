import { useMemo, useState } from 'react'
import { Bot, LayoutGrid, Network } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { AgentCard } from '@/components/dashboard/agent-card'
import { SystemOpsRow } from '@/components/dashboard/system-ops-row'
import { AgentHierarchyTree } from '@/components/agents/agent-hierarchy-tree'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { accentClasses } from '@/lib/accents'
import { cn } from '@/lib/utils'
import { useAgents } from '@/hooks/useAgents'
import type { AgentSummary } from '@/types'

type View = 'grid' | 'hierarchy'

/** Group agents by department in first-seen order, keeping the registry order stable. */
function groupByDepartment(agents: AgentSummary[]): { department: string; agents: AgentSummary[] }[] {
  const order: string[] = []
  const bucket: Record<string, AgentSummary[]> = {}
  for (const agent of agents) {
    if (!bucket[agent.department]) {
      bucket[agent.department] = []
      order.push(agent.department)
    }
    bucket[agent.department].push(agent)
  }
  return order.map((department) => ({ department, agents: bucket[department] }))
}

/** A two-button segmented control toggling between the Grid and Hierarchy views. */
function ViewToggle({ view, onChange }: { view: View; onChange: (next: View) => void }) {
  const options: { value: View; label: string; icon: typeof LayoutGrid }[] = [
    { value: 'grid', label: 'Grid', icon: LayoutGrid },
    { value: 'hierarchy', label: 'Hierarchy', icon: Network },
  ]
  return (
    <div className="inline-flex items-center gap-1 rounded-lg border border-white/[0.06] bg-omnivra-surface p-1">
      {options.map(({ value, label, icon: Icon }) => {
        const active = view === value
        return (
          <button
            key={value}
            type="button"
            onClick={() => onChange(value)}
            aria-pressed={active}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors duration-200 ease-out-quint',
              active
                ? 'bg-white/[0.06] text-omnivra-cyan'
                : 'text-zinc-400 hover:text-zinc-200',
            )}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden />
            {label}
          </button>
        )
      })}
    </div>
  )
}

/**
 * Agents — the full roster page. A "AI Agents" SectionHeader (with a live count)
 * and a Grid/Hierarchy segmented toggle. Grid view groups text/media agents by
 * department into glass sections of AgentCards (staggered in) plus a SystemOpsRow
 * for the `kind === 'system'` utilities. Hierarchy view renders the flagship
 * AgentHierarchyTree (React Flow org chart). Renders instantly from the bundled
 * fallback and upgrades to the live GET /agents list.
 */
export function Agents() {
  // useAgents has initialData (the bundled roster), so `agents` is always defined and
  // is the stable React Query reference — safe to use directly in the useMemo deps below.
  const { data: agents } = useAgents()
  const [view, setView] = useState<View>('grid')

  const systemOps = useMemo(() => agents.filter((a) => a.kind === 'system'), [agents])
  const departments = useMemo(
    () => groupByDepartment(agents.filter((a) => a.kind !== 'system')),
    [agents],
  )

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <SectionHeader label="AI Agents" count={agents.length} />
          <ViewToggle view={view} onChange={setView} />
        </div>
      </Reveal>

      {view === 'hierarchy' ? (
        <Reveal delay={0.05}>
          <GlassCard variant="panel" padding="sm">
            <AgentHierarchyTree agents={agents} />
          </GlassCard>
        </Reveal>
      ) : (
        <div className="flex flex-col gap-5">
          {departments.map(({ department, agents: members }, i) => {
            const accent = members[0]?.accent ?? 'cyan'
            const ac = accentClasses(accent)
            return (
              <Reveal key={department} delay={0.04 * i}>
                <GlassCard padding="md">
                  <SectionHeader
                    label={department}
                    count={members.length}
                    action={
                      <span className={cn('text-[11px] font-medium uppercase tracking-wide', ac.text)}>
                        Department
                      </span>
                    }
                  />
                  <Stagger className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6">
                    {members.map((agent) => (
                      <StaggerItem key={agent.id}>
                        <AgentCard agent={agent} />
                      </StaggerItem>
                    ))}
                  </Stagger>
                </GlassCard>
              </Reveal>
            )
          })}

          {systemOps.length > 0 && (
            <Reveal delay={0.04 * departments.length}>
              <GlassCard padding="md">
                <SectionHeader label="System Operations" count={systemOps.length} />
                <div className="mt-1">
                  <SystemOpsRow ops={systemOps} />
                </div>
              </GlassCard>
            </Reveal>
          )}

          {agents.length === 0 && (
            <GlassCard padding="lg" className="flex items-center justify-center gap-2 text-sm text-zinc-500">
              <Bot className="h-4 w-4" aria-hidden />
              No agents registered yet.
            </GlassCard>
          )}
        </div>
      )}
    </div>
  )
}
