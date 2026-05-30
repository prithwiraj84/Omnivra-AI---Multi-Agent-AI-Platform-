import type { CSSProperties } from 'react'
import { cn } from '@/lib/utils'
import { accentHex } from '@/styles/tokens'
import type { Accent } from '@/types'

export interface ProgressBarProps {
  /** Progress value, 0–100. */
  value: number
  /** Accent color driving the fill + its glow (default `cyan`). */
  accent?: Accent
  /** Show a right-aligned `%` label above/beside the track. */
  showLabel?: boolean
  /** Extra classes for the track element. */
  trackClassName?: string
  /** Extra classes for the outer wrapper. */
  className?: string
}

/**
 * ProgressBar — a thin animated bar built on `.progress-track` + `.progress-fill`.
 * The fill color and its neon glow are driven by the `--bar` CSS variable, set
 * inline from `accentHex` so CSS + JS never drift.
 */
export function ProgressBar({
  value,
  accent = 'cyan',
  showLabel = false,
  trackClassName,
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value))
  const fillStyle = { '--bar': accentHex[accent], width: `${clamped}%` } as CSSProperties

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {showLabel && (
        <div className="flex justify-end">
          <span className="tabular text-xs font-medium text-[#71717a]">
            {Math.round(clamped)}%
          </span>
        </div>
      )}
      <div
        className={cn('progress-track', trackClassName)}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="progress-fill" style={fillStyle} />
      </div>
    </div>
  )
}
