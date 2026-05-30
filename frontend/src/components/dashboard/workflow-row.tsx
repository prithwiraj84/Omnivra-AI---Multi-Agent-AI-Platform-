import { IconTile } from '@/components/ui/icon-tile'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { ProgressBar } from '@/components/ui/progress-bar'
import type { WorkflowItem, WorkflowStatus } from '@/types'

export interface WorkflowRowProps {
  workflow: WorkflowItem
}

/**
 * Status → NeonBadge tone. `Queued` → neutral resolves to the same `.badge-info`
 * recipe (NeonBadge's tone union has no `neutral`), keeping the mapping type-safe.
 */
const statusTone: Record<WorkflowStatus, BadgeTone> = {
  Completed: 'success',
  Review: 'info',
  'In Progress': 'warning',
  Failed: 'danger',
  Queued: 'info',
}

/**
 * WorkflowRow — one active-workflow line: tinted IconTile, a name + department
 * block, and a right block stacking the status badge over a labelled progress bar.
 */
export function WorkflowRow({ workflow }: WorkflowRowProps) {
  const { name, department, status, progress, accent, icon } = workflow
  return (
    <div className="flex items-center gap-3 py-3">
      <IconTile accent={accent} icon={icon} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-[#fafafa]">{name}</p>
        <p className="truncate text-xs text-[#a1a1aa]">{department}</p>
      </div>
      <div className="flex w-36 shrink-0 flex-col items-end gap-2">
        <NeonBadge tone={statusTone[status]} dot>
          {status}
        </NeonBadge>
        <ProgressBar value={progress} accent={accent} showLabel className="w-full" />
      </div>
    </div>
  )
}
