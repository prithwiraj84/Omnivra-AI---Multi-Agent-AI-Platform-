import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  type TooltipProps,
} from 'recharts'
import { chart, text } from '@/styles/tokens'

export interface DonutDatum {
  name: string
  value: number
  color: string
}

export interface OmniDonutChartProps {
  data: DonutDatum[]
  centerValue?: string | number
  centerLabel?: string
  height?: number
}

/** Dark glass tooltip for a single donut slice. */
function DonutTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  const slice = payload[0]
  const color = (slice.payload as DonutDatum | undefined)?.color ?? slice.color
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs shadow-lg backdrop-blur"
      style={{
        background: chart.tooltipBg,
        border: `1px solid ${chart.tooltipBorder}`,
        color: text.secondary,
      }}
    >
      <div className="flex items-center gap-2">
        <span
          className="inline-block h-2 w-2 rounded-full"
          style={{ background: color, boxShadow: `0 0 6px -1px ${color}` }}
        />
        <span style={{ color: text.muted }}>{slice.name}</span>
        <span className="ml-auto font-mono font-medium" style={{ color: text.primary }}>
          {slice.value}
        </span>
      </div>
    </div>
  )
}

/**
 * OmniDonutChart — donut (Pie with inner radius ~70%) for "Task Distribution". Slices use the
 * caller-supplied categorical colors; an absolutely-positioned overlay shows a center value +
 * label. Renders only the chart; the caller supplies the container/GlassCard.
 */
export function OmniDonutChart({
  data,
  centerValue,
  centerLabel,
  height = 240,
}: OmniDonutChartProps) {
  return (
    <div className="relative" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip cursor={false} content={<DonutTooltip />} />
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius="70%"
            outerRadius="100%"
            paddingAngle={2}
            stroke="none"
            startAngle={90}
            endAngle={-270}
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      {(centerValue !== undefined || centerLabel) && (
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          {centerValue !== undefined && (
            <span
              className="font-mono text-2xl font-semibold leading-none"
              style={{ color: text.primary }}
            >
              {centerValue}
            </span>
          )}
          {centerLabel && (
            <span className="mt-1 text-[11px] uppercase tracking-wider" style={{ color: text.faint }}>
              {centerLabel}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
