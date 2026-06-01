import type { ModelUsageItem } from '@/types'
import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { BarMeter } from '@/components/ui/charts/bar-meter'
import { Button } from '@/components/ui/button'
import { Reveal } from '@/components/common/reveal'

export interface ModelUsageProps {
  models: ModelUsageItem[]
  onViewAll?: () => void
}

/**
 * ModelUsage — "Top Models By Usage" card: a BarMeter keyed by full model id
 * (rendered in mono + truncated by BarMeter), with a "View All" action.
 */
export function ModelUsage({ models, onViewAll }: ModelUsageProps) {
  return (
    <Reveal>
      <GlassCard className="space-y-4">
        <SectionHeader
          label="Top Models By Usage"
          action={
            <Button variant="ghost" size="sm" onClick={onViewAll}>
              View All
            </Button>
          }
        />
        {models.length === 0 ? (
          <p className="py-8 text-center text-xs text-zinc-500">No model usage yet — appears as workflows run.</p>
        ) : (
          <BarMeter
            className="[&_li_span:first-child]:font-mono"
            rows={models.map((m) => ({
              label: m.id,
              pct: m.pct,
              value: `${m.calls} calls`,
              color: m.color,
            }))}
          />
        )}
      </GlassCard>
    </Reveal>
  )
}
