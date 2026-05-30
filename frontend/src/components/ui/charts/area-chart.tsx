import { useId } from 'react'
import {
  Area,
  AreaChart as RechartsAreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipProps,
} from 'recharts'
import { chart, text } from '@/styles/tokens'

export interface AreaChartSeries {
  key: string
  label: string
  color: string
}

export interface OmniAreaChartProps {
  data: Array<Record<string, number | string>>
  xKey: string
  series: AreaChartSeries[]
  height?: number
}

/** Dark glass tooltip shared by the area chart. Keyed by series so labels follow the data. */
function AreaTooltip({
  active,
  payload,
  label,
  series,
}: TooltipProps<number, string> & { series: AreaChartSeries[] }) {
  if (!active || !payload?.length) return null
  const labelFor = (key: string | number | undefined) =>
    series.find((s) => s.key === key)?.label ?? String(key ?? '')
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs shadow-lg backdrop-blur"
      style={{
        background: chart.tooltipBg,
        border: `1px solid ${chart.tooltipBorder}`,
        color: text.secondary,
      }}
    >
      <div className="mb-1.5 font-medium" style={{ color: text.muted }}>
        {String(label ?? '')}
      </div>
      <div className="space-y-1">
        {payload.map((entry) => (
          <div key={String(entry.dataKey)} className="flex items-center gap-2">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: entry.color, boxShadow: `0 0 6px -1px ${entry.color}` }}
            />
            <span style={{ color: text.muted }}>{labelFor(entry.dataKey)}</span>
            <span className="ml-auto font-mono font-medium" style={{ color: text.primary }}>
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * OmniAreaChart — multi-area chart (Completed / In Progress / Failed) for "Task Execution
 * Overview". Each series draws a stroke with a top→transparent gradient fill. Renders only the
 * chart; the caller supplies the container/GlassCard.
 */
export function OmniAreaChart({ data, xKey, series, height = 280 }: OmniAreaChartProps) {
  const gradientPrefix = useId()
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsAreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <defs>
          {series.map((s) => {
            const id = `${gradientPrefix}-${s.key}`
            return (
              <linearGradient key={s.key} id={id} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={s.color} stopOpacity={0.32} />
                <stop offset="100%" stopColor={s.color} stopOpacity={0} />
              </linearGradient>
            )
          })}
        </defs>
        <CartesianGrid vertical={false} stroke={chart.grid} strokeDasharray="3 3" />
        <XAxis
          dataKey={xKey}
          tickLine={false}
          axisLine={false}
          tick={{ fill: chart.axis, fontSize: 11 }}
          tickMargin={10}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tick={{ fill: chart.axis, fontSize: 11 }}
          width={40}
        />
        <Tooltip
          cursor={{ stroke: chart.tooltipBorder, strokeWidth: 1 }}
          content={<AreaTooltip series={series} />}
        />
        {series.map((s) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={s.color}
            strokeWidth={2}
            fill={`url(#${gradientPrefix}-${s.key})`}
            fillOpacity={1}
            activeDot={{ r: 4, strokeWidth: 0 }}
            dot={false}
          />
        ))}
      </RechartsAreaChart>
    </ResponsiveContainer>
  )
}
