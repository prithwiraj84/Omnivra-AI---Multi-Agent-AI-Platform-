import { IconTile } from '@/components/ui/icon-tile'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { ApprovalItem, Priority } from '@/types'

/** Approval-gate decision actions (mirrors the backend decision contract). */
export type ApprovalAction = 'approve' | 'reject' | 'retry' | 'rollback'

export interface ApprovalCardProps {
  item: ApprovalItem
  onReview?: (id: string) => void
  /** When provided, render the four decision buttons instead of the Review button. */
  onDecision?: (action: ApprovalAction) => void
  /** Disable the decision buttons while a decision is in flight. */
  busy?: boolean
}

/** Priority → NeonBadge tone (high = danger, medium = warning, low = info). */
const priorityTone: Record<Priority, BadgeTone> = {
  high: 'danger',
  medium: 'warning',
  low: 'info',
}

/** Capitalize the priority for the badge label ("high" → "High"). */
function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

/** Decision button definitions, in render order, with their on-brand accent classes. */
const DECISION_BUTTONS: { action: ApprovalAction; label: string; className: string }[] = [
  {
    action: 'approve',
    label: 'Approve',
    className: 'border-omnivra-emerald/40 text-omnivra-emerald hover:bg-omnivra-emerald/10',
  },
  {
    action: 'reject',
    label: 'Reject',
    className: 'border-omnivra-pink/40 text-omnivra-pink hover:bg-omnivra-pink/10',
  },
  {
    action: 'retry',
    label: 'Retry',
    className: 'border-omnivra-amber/40 text-omnivra-amber hover:bg-omnivra-amber/10',
  },
  {
    action: 'rollback',
    label: 'Rollback',
    className: 'border-omnivra-purple/40 text-omnivra-purple hover:bg-omnivra-purple/10',
  },
]

/**
 * ApprovalCard — a single pending-approval row: tinted icon tile, the item title
 * with its source, a priority NeonBadge, and an action area. By default the action
 * area is a compact "Review" button; when `onDecision` is provided it shows four
 * small accent action buttons (Approve / Reject / Retry / Rollback) wired to the gate.
 */
export function ApprovalCard({ item, onReview, onDecision, busy }: ApprovalCardProps) {
  return (
    <div className="flex items-center gap-3">
      <IconTile accent={item.accent} size="sm" icon={item.icon} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-zinc-200">{item.title}</p>
        <p className="truncate text-xs text-zinc-400">{item.source}</p>
      </div>
      <NeonBadge tone={priorityTone[item.priority]}>{capitalize(item.priority)}</NeonBadge>
      {onDecision ? (
        <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
          {DECISION_BUTTONS.map(({ action, label, className }) => (
            <Button
              key={action}
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() => onDecision(action)}
              className={cn(className)}
            >
              {label}
            </Button>
          ))}
        </div>
      ) : (
        <Button size="sm" variant="outline" onClick={() => onReview?.(item.id)}>
          Review
        </Button>
      )}
    </div>
  )
}
