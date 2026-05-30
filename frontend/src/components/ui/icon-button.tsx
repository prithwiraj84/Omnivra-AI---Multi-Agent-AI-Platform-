import { forwardRef } from 'react'
import type { ButtonHTMLAttributes } from 'react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Lucide icon to render in the button. */
  icon: LucideIcon
  /** Accessible label (required — the button has no visible text). */
  'aria-label': string
  /** Optional count rendered as a small red badge in the top-right. */
  badge?: number
}

/**
 * IconButton — a ghost square button (surface-2 on hover) wrapping a single
 * Lucide icon, with an optional small red count badge. Forwards its ref to the
 * underlying `<button>`.
 */
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ icon: Icon, badge, className, type = 'button', ...props }, ref) => {
    const showBadge = badge !== undefined && badge > 0
    return (
      <button
        ref={ref}
        type={type}
        className={cn(
          'focus-ring relative inline-flex h-9 w-9 items-center justify-center rounded-xl text-[#a1a1aa] transition-colors duration-200 ease-out-quint hover:bg-omnivra-surface-2 hover:text-white disabled:pointer-events-none disabled:opacity-50',
          className,
        )}
        {...props}
      >
        <Icon className="h-[18px] w-[18px]" />
        {showBadge && (
          <span className="tabular absolute -right-0.5 -top-0.5 inline-flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-omnivra-red px-1 text-[10px] font-semibold leading-none text-white shadow-[0_0_8px_-1px_rgba(239,68,68,0.7)]">
            {badge > 99 ? '99+' : badge}
          </span>
        )}
      </button>
    )
  },
)
IconButton.displayName = 'IconButton'
