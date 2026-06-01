import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { OmniDonutChart } from '@/components/ui/charts/donut-chart'
import { Reveal } from '@/components/common/reveal'
import type { DistributionSlice } from '@/types'

export interface TaskDistributionProps {
  data: DistributionSlice[]
  total: number
}

/**
 * TaskDistribution — "Task Distribution" panel: a donut chart (total in the
 * center) with a legend list of colored-dot rows, each showing its share %.
 */
export function TaskDistribution({ data, total }: TaskDistributionProps) {
  return (
    <GlassCard variant="panel">
      <SectionHeader label="Task Distribution" />
      {data.length === 0 ? (
        <p className="py-12 text-center text-xs text-zinc-500">No tasks yet — distribution by project appears here.</p>
      ) : (
        <>
      <Reveal className="mt-4">
        <OmniDonutChart data={data} centerValue={total} centerLabel="Total Tasks" height={240} />
      </Reveal>
      <ul className="mt-4 space-y-2.5">
        {data.map((slice) => (
          <li key={slice.name} className="flex items-center gap-2.5">
            <span
              className="inline-block h-2 w-2 shrink-0 rounded-full"
              style={{ background: slice.color, boxShadow: `0 0 6px -1px ${slice.color}` }}
              aria-hidden
            />
            <span className="min-w-0 flex-1 truncate text-sm text-[#e4e4e7]">{slice.name}</span>
            <span className="tabular shrink-0 text-sm font-medium text-[#fafafa]">{slice.value}%</span>
          </li>
        ))}
      </ul>
        </>
      )}
    </GlassCard>
  )
}
