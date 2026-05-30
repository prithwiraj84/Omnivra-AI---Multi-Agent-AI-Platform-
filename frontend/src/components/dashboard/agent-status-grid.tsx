import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { AgentCard } from '@/components/dashboard/agent-card'
import { SystemOpsRow } from '@/components/dashboard/system-ops-row'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import type { AgentSummary } from '@/types'

export interface AgentStatusGridProps {
  agents: AgentSummary[]
  systemOps: AgentSummary[]
  onViewAll?: () => void
}

/**
 * AgentStatusGrid — the "AI Agents Status" cluster: a responsive grid of
 * AgentCard tiles with a "View All Agents" action, plus the SystemOpsRow
 * sub-panel. Presentational; the assembler supplies `agents`/`systemOps`.
 */
export function AgentStatusGrid({ agents, systemOps, onViewAll }: AgentStatusGridProps) {
  return (
    <GlassCard padding="md">
      <SectionHeader
        label="AI Agents Status"
        count={agents.length}
        action={
          <button
            type="button"
            onClick={onViewAll}
            className="text-xs font-medium text-omnivra-cyan transition-colors hover:text-omnivra-cyan/80"
          >
            View All Agents
          </button>
        }
      />
      <Stagger className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6">
        {agents.map((agent) => (
          <StaggerItem key={agent.id}>
            <AgentCard agent={agent} />
          </StaggerItem>
        ))}
      </Stagger>
      <SystemOpsRow ops={systemOps} />
    </GlassCard>
  )
}
