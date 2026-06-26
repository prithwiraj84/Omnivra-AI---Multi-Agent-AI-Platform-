import { cn } from '@/lib/utils'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import { ActivityFeed } from '@/components/dashboard/activity-feed'
import { PendingApprovals } from '@/components/dashboard/pending-approvals'
import { SystemHealth } from '@/components/dashboard/system-health'
import { BrandFooterCard } from '@/components/dashboard/brand-footer-card'
import { useDashboard } from '@/hooks/useDashboard'

export type RightRailProps = React.HTMLAttributes<HTMLElement>

/**
 * RightRail — the 320px context rail (hidden below `xl`). Hosts the live Phase-3/4
 * sections: Live Activity Feed, Pending Approvals, System Health, and the brand footer.
 * Data comes from useDashboard() (shared, deduped query) — fallback instantly, live when
 * the backend is up. The clock lives in GreetingHero, so the rail no longer shows it.
 */
export function RightRail({ className, ...props }: RightRailProps) {
  const { data } = useDashboard()

  return (
    <aside
      className={cn(
        // h-full fills the viewport-height rail track so its cards sit on-screen; overflow-y-auto is
        // a graceful fallback (no scrollbar when the four cards fit, which they do on a normal screen).
        'hidden h-full w-[320px] shrink-0 flex-col gap-4 overflow-y-auto scroll-thin border-l border-white/[0.08] p-4 xl:flex',
        className,
      )}
      {...props}
    >
      <Stagger className="flex flex-col gap-4">
        <StaggerItem>
          <ActivityFeed items={data.activity} />
        </StaggerItem>
        <StaggerItem>
          <PendingApprovals items={data.approvals} total={data.totalPendingApprovals} />
        </StaggerItem>
        <StaggerItem>
          <SystemHealth metrics={data.systemHealth} />
        </StaggerItem>
        <StaggerItem>
          <BrandFooterCard />
        </StaggerItem>
      </Stagger>
    </aside>
  )
}
