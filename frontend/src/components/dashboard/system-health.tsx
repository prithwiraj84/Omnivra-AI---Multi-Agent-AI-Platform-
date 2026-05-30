import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { ProgressBar } from '@/components/ui/progress-bar'
import { NeonBadge } from '@/components/ui/neon-badge'
import type { HealthMetric } from '@/types'

export interface SystemHealthProps {
  metrics: HealthMetric[]
}

/**
 * SystemHealth — the right-rail "System Health" panel. Each metric shows its label
 * with the value on the right. Numeric metrics (`pct != null`) render an accent
 * ProgressBar beneath the label; the non-numeric Network metric shows a success badge.
 */
export function SystemHealth({ metrics }: SystemHealthProps) {
  return (
    <GlassCard padding="md">
      <SectionHeader
        label="System Health"
        action={
          <button
            type="button"
            className="text-xs font-medium text-omnivra-cyan transition-colors hover:brightness-110"
          >
            View All
          </button>
        }
        className="mb-4"
      />

      <div className="flex flex-col gap-3.5">
        {metrics.map((metric) =>
          metric.pct != null ? (
            <div key={metric.label} className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-400">{metric.label}</span>
                <span className="tabular text-xs font-medium text-zinc-200">{metric.display}</span>
              </div>
              <ProgressBar value={metric.pct} accent={metric.accent} />
            </div>
          ) : (
            <div key={metric.label} className="flex items-center justify-between">
              <span className="text-xs text-zinc-400">{metric.label}</span>
              <NeonBadge tone="success">{metric.display}</NeonBadge>
            </div>
          ),
        )}
      </div>
    </GlassCard>
  )
}
