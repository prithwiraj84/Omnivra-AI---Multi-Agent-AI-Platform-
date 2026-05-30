import type { AchievementItem } from '@/types'
import { SectionHeader } from '@/components/ui/section-header'
import { AchievementCard } from '@/components/dashboard/achievement-card'
import { Stagger, StaggerItem } from '@/components/common/reveal'

export interface AchievementsProps {
  items: AchievementItem[]
}

/**
 * Achievements — "Recent Achievements" section: a SectionHeader over a responsive
 * grid of AchievementCard tiles (2 / 3 / 5 columns).
 */
export function Achievements({ items }: AchievementsProps) {
  return (
    <section className="space-y-4">
      <SectionHeader label="Recent Achievements" />
      <Stagger className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        {items.map((item) => (
          <StaggerItem key={item.title} className="h-full">
            <AchievementCard item={item} />
          </StaggerItem>
        ))}
      </Stagger>
    </section>
  )
}
