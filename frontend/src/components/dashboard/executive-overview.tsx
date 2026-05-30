import { StatCard } from '@/components/dashboard/stat-card'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import type { StatCardData } from '@/types'

export interface ExecutiveOverviewProps {
  stats: StatCardData[]
}

/**
 * ExecutiveOverview — the responsive 5-card stat row. Presentational: the
 * assembler passes `stats` in so Phase 4 can swap mock data for live metrics.
 */
export function ExecutiveOverview({ stats }: ExecutiveOverviewProps) {
  return (
    <Stagger className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
      {stats.map((stat) => (
        <StaggerItem key={stat.label}>
          <StatCard {...stat} />
        </StaggerItem>
      ))}
    </Stagger>
  )
}
