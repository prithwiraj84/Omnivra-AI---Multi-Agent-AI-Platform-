import type { MediaServiceItem } from '@/types'
import { GlassCard } from '@/components/ui/glass-card'
import { IconTile } from '@/components/ui/icon-tile'
import { NeonBadge } from '@/components/ui/neon-badge'

export interface MediaServiceCardProps {
  service: MediaServiceItem
}

/**
 * MediaServiceCard — one media-service row on a subtle inset surface: an accented
 * IconTile + name/provider on the left, call count + a success delta badge on the right.
 */
export function MediaServiceCard({ service }: MediaServiceCardProps) {
  return (
    <GlassCard
      variant="panel"
      padding="none"
      interactive
      glow={service.accent}
      className="panel-inset flex items-center gap-3 border-transparent p-3 shadow-none"
    >
      <IconTile accent={service.accent} icon={service.icon} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-[#fafafa]">{service.name}</p>
        <p className="truncate text-xs text-[#a1a1aa]">{service.provider}</p>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <span className="tabular text-sm font-semibold text-[#fafafa]">{service.calls}</span>
        <NeonBadge tone="success">{service.delta}</NeonBadge>
      </div>
    </GlassCard>
  )
}
