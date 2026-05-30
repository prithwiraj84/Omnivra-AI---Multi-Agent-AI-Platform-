import type { CSSProperties } from 'react'
import { cn } from '@/lib/utils'
import { text } from '@/styles/tokens'

export interface BarMeterRow {
  label: string
  pct: number
  value?: string
  color: string
}

export interface BarMeterProps {
  rows: BarMeterRow[]
  className?: string
}

/** Clamp a percentage into the renderable 0–100 range. */
function clampPct(pct: number): number {
  if (Number.isNaN(pct)) return 0
  return Math.max(0, Math.min(100, pct))
}

/**
 * BarMeter — a clean list of horizontal meter rows for "Model / Provider usage" lists. Not a
 * Recharts chart: each row pairs a left-aligned label, an animated fill bar over `.progress-track`
 * tinted by the row color, and a right-aligned value/percent.
 */
export function BarMeter({ rows, className }: BarMeterProps) {
  return (
    <ul className={cn('space-y-3.5', className)}>
      {rows.map((row) => {
        const pct = clampPct(row.pct)
        return (
          <li key={row.label}>
            <div className="mb-1.5 flex items-center justify-between gap-3 text-xs">
              <span className="truncate" style={{ color: text.secondary }}>
                {row.label}
              </span>
              <span className="shrink-0 font-mono font-medium" style={{ color: text.muted }}>
                {row.value ?? `${Math.round(pct)}%`}
              </span>
            </div>
            <div className="progress-track">
              <div
                className="progress-fill"
                style={{ width: `${pct}%`, ['--bar' as keyof CSSProperties]: row.color } as CSSProperties}
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
