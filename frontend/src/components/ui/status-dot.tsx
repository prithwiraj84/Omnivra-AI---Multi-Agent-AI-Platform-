import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

/**
 * StatusDot — the glowing 8px presence dot used on agent cards, chips and rows.
 * The dot's color comes from `currentColor` (the `.status-dot` class sets both
 * background and glow to it), so we drive the hue with a literal `text-*` class.
 */
export type DotStatus = 'online' | 'offline' | 'busy' | 'idle' | 'working' | 'needs_approval'

export interface StatusDotProps extends React.HTMLAttributes<HTMLSpanElement> {
  status?: DotStatus
  /** Slow attention pulse (online presence). */
  pulse?: boolean
  /** Optional trailing text; when set, renders dot + label inline. */
  label?: string
}

// Literal color classes so Tailwind's scanner emits them.
const statusColor: Record<DotStatus, string> = {
  online: 'text-omnivra-emerald',
  working: 'text-omnivra-cyan',
  needs_approval: 'text-omnivra-amber',
  busy: 'text-omnivra-amber',
  offline: 'text-omnivra-red',
  idle: 'text-zinc-500',
}

export const StatusDot = forwardRef<HTMLSpanElement, StatusDotProps>(
  ({ status = 'online', pulse = false, label, className, ...props }, ref) => {
    const dot = (
      <span
        className={cn('status-dot shrink-0', statusColor[status], pulse && 'animate-pulse-dot')}
        aria-hidden
      />
    )

    if (!label) {
      return (
        <span
          ref={ref}
          role="status"
          className={cn('inline-flex', className)}
          {...props}
        >
          {dot}
        </span>
      )
    }

    return (
      <span
        ref={ref}
        role="status"
        className={cn('inline-flex items-center gap-1.5 text-xs text-zinc-400', className)}
        {...props}
      >
        {dot}
        <span>{label}</span>
      </span>
    )
  },
)
StatusDot.displayName = 'StatusDot'
