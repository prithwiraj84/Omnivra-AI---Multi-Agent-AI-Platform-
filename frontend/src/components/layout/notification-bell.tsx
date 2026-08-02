/**
 * NotificationBell — the topbar bell, backed by REAL data.
 *
 * It previously rendered a hardcoded "12" badge and did nothing on click. Now the badge counts
 * the workflows genuinely waiting on you, and the dropdown lists those approvals plus recent
 * workspace activity, each item navigating to the page that can act on it.
 */
import { useNavigate } from 'react-router-dom'
import { BadgeCheck, Bell, Inbox } from 'lucide-react'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { IconButton } from '@/components/ui/icon-button'
import { useAwaitingApprovals } from '@/hooks/useApprovals'
import { useDashboard } from '@/hooks/useDashboard'
import { cn } from '@/lib/utils'

const MAX_ACTIVITY = 5

export function NotificationBell({ className }: { className?: string }) {
  const navigate = useNavigate()
  const { data: awaiting } = useAwaitingApprovals()
  const { data: dashboard } = useDashboard()

  const approvals = awaiting ?? []
  const activity = (dashboard?.activity ?? []).slice(0, MAX_ACTIVITY)
  // The badge counts only what NEEDS you — activity is informational, approvals are blocking.
  const pending = approvals.length
  const empty = pending === 0 && activity.length === 0

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <IconButton
          icon={Bell}
          aria-label={pending > 0 ? `Notifications — ${pending} awaiting approval` : 'Notifications'}
          badge={pending || undefined}
          className={className}
        />
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="max-h-[26rem] w-[21rem] overflow-y-auto">
        <DropdownMenuLabel>
          <span className="block text-sm font-semibold normal-case tracking-normal text-[#fafafa]">
            Notifications
          </span>
          <span className="block text-xs font-normal normal-case tracking-normal text-[#a1a1aa]">
            {pending > 0
              ? `${pending} workflow${pending === 1 ? '' : 's'} awaiting your approval`
              : 'Nothing needs your approval'}
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {empty && (
          <div className="flex flex-col items-center gap-2 px-4 py-8 text-center">
            <Inbox className="h-6 w-6 text-[#71717a]" aria-hidden />
            <p className="text-xs text-[#a1a1aa]">
              You’re all caught up — approvals and agent activity show up here.
            </p>
          </div>
        )}

        {pending > 0 && (
          <>
            {approvals.slice(0, MAX_ACTIVITY).map((run) => (
              <DropdownMenuItem
                key={run.workflowId}
                onClick={() => navigate('/approvals')}
                className="flex-col items-start gap-0.5"
              >
                <span className="flex w-full items-center gap-2">
                  <BadgeCheck className="h-3.5 w-3.5 shrink-0 text-omnivra-amber" aria-hidden />
                  <span className="truncate text-xs font-medium text-[#e4e4e7]">
                    {run.pendingApproval?.summary || run.task || 'Awaiting approval'}
                  </span>
                </span>
                <span className="pl-[22px] text-[11px] text-[#a1a1aa]">
                  {run.pendingApproval?.requestedBy
                    ? `${run.pendingApproval.requestedBy} · tap to review`
                    : 'Tap to review and decide'}
                </span>
              </DropdownMenuItem>
            ))}
            {activity.length > 0 && <DropdownMenuSeparator />}
          </>
        )}

        {activity.length > 0 && (
          <>
            <DropdownMenuLabel className="pb-1 pt-2 text-[10px]">Recent activity</DropdownMenuLabel>
            {activity.map((item) => (
              <DropdownMenuItem
                key={item.id}
                onClick={() => navigate('/logs')}
                className="flex-col items-start gap-0.5"
              >
                <span className="w-full truncate text-xs text-[#e4e4e7]">
                  <span className="font-medium">{item.agent}</span> {item.action}
                </span>
                <span className="text-[11px] text-[#a1a1aa]">{item.time}</span>
              </DropdownMenuItem>
            ))}
          </>
        )}

        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => navigate(pending > 0 ? '/approvals' : '/logs')}
          className={cn('justify-center text-xs font-medium text-omnivra-cyan')}
        >
          {pending > 0 ? 'Review all approvals' : 'View all activity'}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
