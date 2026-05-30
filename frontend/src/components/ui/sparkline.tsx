import { useId } from 'react'
import { Area, AreaChart, ResponsiveContainer } from 'recharts'
import { cn } from '@/lib/utils'
import { accentHex } from '@/styles/tokens'
import type { Accent } from '@/types'

export interface SparklineProps {
  /** Series of y-values; rendered as a tiny filled area chart. */
  data: number[]
  /** Accent color for stroke + gradient fill (default `cyan`). */
  accent?: Accent
  /** Width in px (default 96). */
  width?: number
  /** Height in px (default 28). */
  height?: number
  /** Extra classes for the wrapper. */
  className?: string
}

/**
 * Sparkline — a minimal Recharts area chart (no axes/grid/tooltip) with an
 * accent-colored gradient fill. Sized via `width`/`height` props.
 */
export function Sparkline({ data, accent = 'cyan', width = 96, height = 28, className }: SparklineProps) {
  const id = useId()
  const gradientId = `spark-${id}`
  const color = accentHex[accent]
  const chartData = data.map((value, index) => ({ index, value }))

  return (
    <div className={cn('inline-block', className)} style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            fill={`url(#${gradientId})`}
            isAnimationActive={false}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
