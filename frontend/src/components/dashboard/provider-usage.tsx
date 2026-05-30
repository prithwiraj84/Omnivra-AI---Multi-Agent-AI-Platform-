import type { ProviderUsageItem } from '@/types'
import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { BarMeter } from '@/components/ui/charts/bar-meter'
import { Reveal } from '@/components/common/reveal'

export interface ProviderUsageProps {
  providers: ProviderUsageItem[]
}

/**
 * ProviderUsage — "Model Usage (By Provider)" card: a BarMeter of provider call
 * volumes (Google AI / OpenRouter / Groq / Hugging Face), each tinted by its color.
 */
export function ProviderUsage({ providers }: ProviderUsageProps) {
  return (
    <Reveal>
      <GlassCard className="space-y-4">
        <SectionHeader label="Model Usage (By Provider)" />
        <BarMeter
          rows={providers.map((p) => ({
            label: p.name,
            pct: p.pct,
            value: `${p.calls} calls`,
            color: p.color,
          }))}
        />
      </GlassCard>
    </Reveal>
  )
}
