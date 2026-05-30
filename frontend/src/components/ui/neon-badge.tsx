import { forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { toneBadgeClass } from '@/lib/accents'

/**
 * NeonBadge — the small neon pill used for statuses, counts and labels.
 * Tone selects one of the `.badge-*` color recipes from `index.css`; an optional
 * leading dot inherits the badge's text color via `currentColor`.
 */
export type BadgeTone = 'success' | 'info' | 'warning' | 'danger' | 'cyan' | 'violet'

export interface NeonBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone
  /** Leading status dot tinted to the badge color. */
  dot?: boolean
}

export const NeonBadge = forwardRef<HTMLSpanElement, NeonBadgeProps>(
  ({ tone = 'info', dot = false, className, children, ...props }, ref) => (
    <span ref={ref} className={cn('badge', toneBadgeClass[tone], className)} {...props}>
      {dot && (
        <span
          className="h-1.5 w-1.5 shrink-0 rounded-full bg-current shadow-[0_0_6px_0_currentColor]"
          aria-hidden
        />
      )}
      {children}
    </span>
  ),
)
NeonBadge.displayName = 'NeonBadge'
