import { useNavigate } from 'react-router-dom'
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
  const navigate = useNavigate()
  return (
    <GlassCard className="flex h-full flex-col">
      <SectionHeader
        label="Active Workflows"
        action={
          <Button variant="ghost" size="sm" className="px-2 text-omnivra-cyan" onClick={onViewAll ?? (() => navigate('/workflows'))}>
            View All
          </Button>
        }
      />
      {workflows.length === 0 ? (
        <p className="flex flex-1 items-center justify-center px-4 py-10 text-center text-xs text-zinc-500">No active workflows yet — they appear here as tasks run.</p>
      ) : (
        <Stagger className="mt-2 divide-y divide-white/5">
          {workflows.map((workflow) => (
            <StaggerItem key={workflow.id}>
              <WorkflowRow workflow={workflow} />
            </StaggerItem>
          ))}
        </Stagger>
      )}
    </GlassCard>
  )
}
