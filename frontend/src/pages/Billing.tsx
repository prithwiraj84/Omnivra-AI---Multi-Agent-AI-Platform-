import { Coins, DollarSign, Layers } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { IconTile } from '@/components/ui/icon-tile'
import { BarMeter } from '@/components/ui/charts/bar-meter'
import { EmptyState } from '@/components/ui/empty-state'
import { Reveal } from '@/components/common/reveal'
import { CountUp } from '@/components/common/count-up'
import { useDashboard } from '@/hooks/useDashboard'

/**
 * Billing — a read-only cost / usage view. Surfaces the dashboard's Total Cost
 * stat as a headline figure, then breaks usage down two ways: "Model Usage (By
 * Provider)" as a BarMeter of provider call-share, and "Top Models" as a BarMeter
 * of the most-used models by call volume. All data comes from useDashboard()
 * (bundled fallback offline, live GET /api/dashboard when the backend is up).
 */
export function Billing() {
  const { data: dashboard } = useDashboard()

  const costStat = dashboard?.stats.find((s) => /cost/i.test(s.label))
  const providerUsage = dashboard?.providerUsage ?? []
  const modelUsage = dashboard?.modelUsage ?? []

  const providerRows = providerUsage.map((p) => ({
    label: p.name,
    pct: p.pct,
    value: `${p.calls.toLocaleString('en-US')} calls`,
    color: p.color,
  }))

  const modelRows = modelUsage.map((m) => ({
    label: m.id,
    pct: m.pct,
    value: `${m.calls.toLocaleString('en-US')} calls`,
    color: m.color,
  }))

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <GlassCard padding="md" glow="violet" className="flex items-center gap-4">
          <IconTile accent="violet" icon={DollarSign} />
          <div className="flex flex-col">
            <span className="section-label">{costStat?.label ?? 'Total Cost (Est.)'}</span>
            <CountUp
              value={costStat?.value ?? '$0.00'}
              className="text-3xl font-semibold tabular text-zinc-100"
            />
            {costStat?.sub && <span className="text-xs text-[#71717a]">{costStat.sub}</span>}
          </div>
        </GlassCard>
      </Reveal>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Reveal delay={0.05}>
          <GlassCard padding="md" className="flex flex-col gap-4">
            <SectionHeader label="Model Usage (By Provider)" count={providerRows.length} />
            {providerRows.length === 0 ? (
              <EmptyState
                icon={Layers}
                title="No usage yet"
                hint="Provider call-share appears here once agents start running."
                className="py-12"
              />
            ) : (
              <BarMeter rows={providerRows} />
            )}
          </GlassCard>
        </Reveal>

        <Reveal delay={0.1}>
          <GlassCard padding="md" className="flex flex-col gap-4">
            <SectionHeader label="Top Models" count={modelRows.length} />
            {modelRows.length === 0 ? (
              <EmptyState
                icon={Coins}
                title="No model usage yet"
                hint="The most-used models by call volume appear here after a few runs."
                className="py-12"
              />
            ) : (
              <BarMeter rows={modelRows} />
            )}
          </GlassCard>
        </Reveal>
      </div>
    </div>
  )
}
