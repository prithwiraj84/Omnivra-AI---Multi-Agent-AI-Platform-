import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { TimeframeSelect } from '@/components/ui/timeframe-select'
import { OmniAreaChart, type AreaChartSeries } from '@/components/ui/charts/area-chart'
import { Reveal } from '@/components/common/reveal'
import type { TaskPoint } from '@/types'

export interface TaskExecutionChartProps {
  data: TaskPoint[]
  series: AreaChartSeries[]
  timeframe?: string
  onTimeframeChange?: (value: string) => void
}

const TIMEFRAMES = ['Daily', 'Weekly', 'Monthly']

/**
 * TaskExecutionChart — "Task Execution Overview" panel: a SectionHeader with a
 * timeframe dropdown, the stacked-series area chart, and a colored-dot legend.
 */
export function TaskExecutionChart({
  data,
  series,
  timeframe,
  onTimeframeChange,
}: TaskExecutionChartProps) {
  // OmniAreaChart wants plain index-signature records; spread each named TaskPoint.
  const chartData: Record<string, number | string>[] = data.map((point) => ({ ...point }))
  return (
    <GlassCard variant="panel">
      <SectionHeader
        label="Task Execution Overview"
        action={
          <TimeframeSelect
            value={timeframe ?? 'Daily'}
            options={TIMEFRAMES}
            onChange={onTimeframeChange}
          />
        }
      />
      <Reveal className="mt-4">
        <OmniAreaChart data={chartData} xKey="time" series={series} height={260} />
      </Reveal>
      <div className="mt-3 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
        {series.map((s) => (
          <div key={s.key} className="flex items-center gap-2">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: s.color, boxShadow: `0 0 6px -1px ${s.color}` }}
              aria-hidden
            />
            <span className="text-xs text-[#a1a1aa]">{s.label}</span>
          </div>
        ))}
      </div>
    </GlassCard>
  )
}
