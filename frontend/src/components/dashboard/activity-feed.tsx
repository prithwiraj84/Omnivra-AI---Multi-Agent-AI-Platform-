import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { ScrollArea } from '@/components/ui/scroll-area'
import { StatusDot } from '@/components/ui/status-dot'
import { IconTile } from '@/components/ui/icon-tile'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import type { ActivityItem } from '@/types'

export interface ActivityFeedProps {
  items: ActivityItem[]
}

/**
 * ActivityFeed — the "Live Activity Feed" right-rail panel: a scrollable list of
 * recent agent actions, each with a tinted icon tile, the agent name + action,
 * and a faint relative timestamp. A pulsing emerald dot by the header signals "live".
 */
export function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <GlassCard padding="md">
      <SectionHeader
        label="Live Activity Feed"
        action={
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5">
              <StatusDot status="online" pulse aria-label="Live" />
              <span className="text-[11px] font-medium text-omnivra-emerald-bright">Live</span>
            </span>
            <button
              type="button"
              className="text-xs font-medium text-omnivra-cyan transition-colors hover:brightness-110"
            >
              View All
            </button>
          </div>
        }
        className="mb-4"
      />

      <ScrollArea className="max-h-[360px] pr-2">
        {items.length === 0 ? (
          <p className="py-10 text-center text-xs text-zinc-500">No recent activity — agent artifacts appear here as they're written.</p>
        ) : (
          <Stagger className="flex flex-col gap-2.5">
            {items.map((item) => (
              <StaggerItem key={item.id} className="flex items-start gap-3">
                <IconTile accent={item.accent} size="sm" icon={item.icon} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-zinc-200">{item.agent}</p>
                  <p className="truncate text-xs text-zinc-400">{item.action}</p>
                </div>
                <span className="shrink-0 text-xs text-zinc-500">{item.time}</span>
              </StaggerItem>
            ))}
          </Stagger>
        )}
      </ScrollArea>
    </GlassCard>
  )
}
