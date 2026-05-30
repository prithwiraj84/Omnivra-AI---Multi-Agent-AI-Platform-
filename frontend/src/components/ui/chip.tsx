import { forwardRef } from 'react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Accent } from '@/types'
import { StatusDot, type DotStatus } from '@/components/ui/status-dot'

/**
 * Chip — compact pill on surface-2 with an optional leading icon and trailing
 * status dot. Used for the System Ops chip row; `active` adds a subtle accent ring.
 */
export interface ChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  label: string
  icon?: LucideIcon
  accent?: Accent
  status?: DotStatus
  /** Highlights the chip with an accent ring + tinted text. */
  active?: boolean
}

// Literal ring/text classes per accent so Tailwind's scanner emits them.
const activeRing: Record<Accent, string> = {
  cyan: 'ring-omnivra-cyan/40 text-omnivra-cyan',
  violet: 'ring-omnivra-purple/40 text-omnivra-purple',
  blue: 'ring-omnivra-blue/40 text-omnivra-blue',
  emerald: 'ring-omnivra-emerald/40 text-omnivra-emerald',
  amber: 'ring-omnivra-amber/40 text-omnivra-amber',
  pink: 'ring-omnivra-pink/40 text-omnivra-pink',
}

export const Chip = forwardRef<HTMLSpanElement, ChipProps>(
  ({ label, icon: Icon, accent = 'cyan', status, active = false, className, ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border border-white/8 bg-omnivra-surface-2 px-2.5 py-1 text-xs font-medium text-zinc-300 transition-colors',
        active && cn('ring-1 ring-inset', activeRing[accent]),
        className,
      )}
      {...props}
    >
      {Icon && <Icon className="h-3.5 w-3.5 shrink-0" strokeWidth={2} aria-hidden />}
      <span className="truncate">{label}</span>
      {status && <StatusDot status={status} className="ml-0.5" />}
    </span>
  ),
)
Chip.displayName = 'Chip'
