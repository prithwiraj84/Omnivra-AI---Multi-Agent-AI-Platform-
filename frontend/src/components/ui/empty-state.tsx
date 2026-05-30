import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface EmptyStateProps {
  /** Lucide icon shown in the centered tile. */
  icon: LucideIcon
  /** Primary title line. */
  title: string
  /** Optional secondary hint line. */
  hint?: string
  /** Extra classes for the wrapper. */
  className?: string
}

/**
 * EmptyState — a centered icon tile + title + optional hint, used for panels
 * that have no data yet.
 */
export function EmptyState({ icon: Icon, title, hint, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 px-6 py-10 text-center',
        className,
      )}
    >
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/[0.04] text-[#71717a] ring-1 ring-white/[0.06]">
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-[#e4e4e7]">{title}</p>
        {hint && <p className="max-w-[26ch] text-xs leading-relaxed text-[#71717a]">{hint}</p>}
      </div>
    </div>
  )
}
