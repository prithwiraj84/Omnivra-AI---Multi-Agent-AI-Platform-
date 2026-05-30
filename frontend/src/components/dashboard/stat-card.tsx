import { cn } from '@/lib/utils'
import { GlassCard } from '@/components/ui/glass-card'
import { IconTile } from '@/components/ui/icon-tile'
import { CountUp } from '@/components/common/count-up'
import { NeonBadge } from '@/components/ui/neon-badge'
import type { BadgeTone } from '@/components/ui/neon-badge'
import type { StatCardData } from '@/types'

export type StatCardProps = StatCardData

/** Map a semantic delta tone onto a NeonBadge tone (NeonBadge has no `neutral`). */
const deltaBadgeTone: Record<NonNullable<StatCardData['deltaTone']>, BadgeTone> = {
  success: 'success',
  info: 'info',
  warning: 'warning',
  danger: 'danger',
  neutral: 'info',
}

/**
 * StatCard — one Executive-Overview metric tile. Top row pairs the uppercase
 * label with a tinted IconTile; the big tabular value sits below; the footer
 * shows either a delta NeonBadge (preferred) or the `sub` hint text.
 */
export function StatCard({ label, value, sub, delta, deltaTone, icon, accent }: StatCardProps) {
  return (
    <GlassCard interactive glow={accent} padding="md" className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <span className="section-label pt-0.5">{label}</span>
        <IconTile accent={accent} size="sm" icon={icon} />
      </div>

      <CountUp
        value={value}
        className="tabular block text-2xl font-bold leading-none text-[#fafafa] xl:text-3xl"
      />

      <div className="flex min-h-[1.25rem] items-center">
        {delta ? (
          <NeonBadge tone={deltaBadgeTone[deltaTone ?? 'neutral']}>{delta}</NeonBadge>
        ) : (
          sub && <span className={cn('text-xs text-[#a1a1aa]')}>{sub}</span>
        )}
      </div>
    </GlassCard>
  )
}
