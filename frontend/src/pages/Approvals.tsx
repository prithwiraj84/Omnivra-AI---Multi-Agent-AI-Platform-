import { ShieldCheck } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { PendingApprovals } from '@/components/dashboard/pending-approvals'
import { Reveal } from '@/components/common/reveal'
import { useDashboard } from '@/hooks/useDashboard'

/**
 * Approvals — the full-page approval gate. The intro panel explains the gate, then
 * <PendingApprovals> renders the LIVE awaiting runs (fetched + wired to Approve /
 * Reject / Retry / Rollback internally) above the dashboard's seed approvals, so the
 * view looks populated even before a run is dispatched. Offline (tests) the live
 * query yields nothing and only the seed items show.
 */
export function Approvals() {
  const { data } = useDashboard()

  return (
    <div className="flex flex-col gap-6">
      <Reveal>
        <GlassCard padding="lg">
          <SectionHeader label="Approval Gate" />
          <p className="mt-1 flex max-w-2xl items-start gap-2 text-sm leading-relaxed text-[#a1a1aa]">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-omnivra-amber" aria-hidden />
            <span>
              High-impact actions pause here for your sign-off. Approve or retry to resume the
              run, reject to halt it, or roll back to undo what an agent already did.
            </span>
          </p>
        </GlassCard>
      </Reveal>

      <Reveal delay={0.05}>
        <PendingApprovals items={data.approvals} total={data.totalPendingApprovals} />
      </Reveal>
    </div>
  )
}
