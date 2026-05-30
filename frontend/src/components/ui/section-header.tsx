import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface SectionHeaderProps {
  /** Uppercase section label (e.g. "AI AGENTS STATUS"). */
  label: string
  /** Optional right-aligned action (e.g. a "View All" link or button). */
  action?: ReactNode
  /** Optional count chip rendered next to the label. */
  count?: number
  /** Extra classes for the outer wrapper. */
  className?: string
}

/**
 * SectionHeader — the uppercase `.section-label` on the left with an optional
 * count chip, and an optional action node pinned to the right.
 */
export function SectionHeader({ label, action, count, className }: SectionHeaderProps) {
  return (
    <div className={cn('flex items-center justify-between gap-3', className)}>
      <div className="flex items-center gap-2">
        <span className="section-label">{label}</span>
        {count !== undefined && (
          <span className="tabular inline-flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-white/[0.06] px-1.5 text-[10px] font-semibold leading-none text-[#a1a1aa]">
            {count}
          </span>
        )}
      </div>
      {action && <div className="flex shrink-0 items-center">{action}</div>}
    </div>
  )
}
