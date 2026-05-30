import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { Button } from '@/components/ui/button'
import { WorkflowRow } from '@/components/dashboard/workflow-row'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import type { WorkflowItem } from '@/types'

export interface WorkflowListProps {
  workflows: WorkflowItem[]
  onViewAll?: () => void
}

/**
 * WorkflowList — "Active Workflows" container: a GlassCard with a SectionHeader
 * ("View All" action) above a divided vertical list of WorkflowRow items.
 */
export function WorkflowList({ workflows, onViewAll }: WorkflowListProps) {
  return (
    <GlassCard>
      <SectionHeader
        label="Active Workflows"
        action={
          <Button variant="ghost" size="sm" className="px-2 text-omnivra-cyan" onClick={onViewAll}>
            View All
          </Button>
        }
      />
      <Stagger className="mt-2 divide-y divide-white/5">
        {workflows.map((workflow) => (
          <StaggerItem key={workflow.id}>
            <WorkflowRow workflow={workflow} />
          </StaggerItem>
        ))}
      </Stagger>
    </GlassCard>
  )
}
