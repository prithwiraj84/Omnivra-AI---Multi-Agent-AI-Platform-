import type { AchievementItem } from '@/types'
import { GlassCard } from '@/components/ui/glass-card'
import { IconTile } from '@/components/ui/icon-tile'

export interface AchievementCardProps {
  item: AchievementItem
}

/**
 * AchievementCard — one "Recent Achievements" tile: an accented IconTile above a
 * bold title and a muted subtitle, on an interactive GlassCard.
 */
export function AchievementCard({ item }: AchievementCardProps) {
  return (
    <GlassCard interactive padding="sm" glow={item.accent} className="h-full space-y-2.5">
      <IconTile accent={item.accent} icon={item.icon} />
      <div>
        <p className="text-sm font-medium text-[#fafafa]">{item.title}</p>
        <p className="mt-0.5 text-xs text-[#a1a1aa]">{item.subtitle}</p>
      </div>
    </GlassCard>
  )
}
