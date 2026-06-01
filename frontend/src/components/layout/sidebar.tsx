import { NavLink, useLocation } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { tBase } from '@/lib/motion'
import { accentClasses } from '@/lib/accents'
import { navGroups } from '@/config/navigation'
import { useUIStore } from '@/store/ui'
import { useAwaitingApprovals } from '@/hooks/useApprovals'
import { BrandLogo } from './brand-logo'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { NeonBadge } from '@/components/ui/neon-badge'
import { ProgressBar } from '@/components/ui/progress-bar'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { NavItem } from '@/types'

/** True when `to` matches the current pathname (exact for "/", prefix otherwise). */
function isActivePath(pathname: string, to: string): boolean {
  if (to === '/') return pathname === '/'
  return pathname === to || pathname.startsWith(`${to}/`)
}

interface NavRowProps {
  item: NavItem
  active: boolean
  collapsed: boolean
}

/** NavLink with framer-motion props (whileHover/whileTap) while keeping router semantics. */
const MotionNavLink = motion.create(NavLink)

function NavRow({ item, active, collapsed }: NavRowProps) {
  const { icon: Icon, label, badge, accent } = item
  const reduce = useReducedMotion()
  // Department/highlighted items tint their icon via the accent map; the active
  // row turns white so the gradient pill reads cleanly.
  const iconAccent = accent && !active ? accentClasses(accent).dot : ''

  // Tasteful micro-motion: nudge the row right on hover (expanded) / a gentle
  // press on tap. Gated on reduced motion. Collapsed rows are icon-only/centered,
  // so we skip the x-nudge there to avoid jitter. Transform-only — no layout shift.
  const motionProps = reduce
    ? {}
    : {
        whileHover: collapsed ? { scale: 1.06 } : { x: 3 },
        whileTap: { scale: 0.97 },
        transition: tBase,
      }

  const row = (
    <MotionNavLink
      to={item.to}
      aria-current={active ? 'page' : undefined}
      {...motionProps}
      className={cn(
        'nav-item group flex items-center text-sm font-medium',
        collapsed ? 'h-10 w-10 justify-center px-0' : 'h-10 gap-3 px-3',
        active && 'nav-active',
      )}
    >
      <Icon
        className={cn('h-[18px] w-[18px] shrink-0', !active && iconAccent)}
        strokeWidth={2}
        aria-hidden
      />
      {!collapsed && (
        <>
          <span className="flex-1 truncate">{label}</span>
          {badge != null && (
            <NeonBadge tone={active ? 'violet' : 'warning'} className="ml-auto shrink-0 tabular">
              {badge}
            </NeonBadge>
          )}
        </>
      )}
    </MotionNavLink>
  )

  if (!collapsed) return row

  return (
    <Tooltip>
      <TooltipTrigger asChild>{row}</TooltipTrigger>
      <TooltipContent side="right">
        <span className="flex items-center gap-2">
          {label}
          {badge != null && <span className="tabular text-omnivra-amber">{badge}</span>}
        </span>
      </TooltipContent>
    </Tooltip>
  )
}

/**
 * Sidebar — the fixed left rail. Renders the brand mark, a scrollable grouped
 * nav driven by `navGroups`, and a pinned user/plan card with a storage meter.
 * Collapses to a 72px icon rail (label tooltips on hover) from `useUIStore`.
 */
export function Sidebar() {
  const collapsed = useUIStore((s) => s.sidebarCollapsed)
  const { pathname } = useLocation()
  // Live Approvals badge from the real awaiting-runs set (replaces the old hard-coded "7").
  const { data: awaiting } = useAwaitingApprovals()
  const awaitingCount = awaiting?.length ?? 0

  return (
    <aside
      className={cn(
        // In-flow grid item that fills the sidebar column AppLayout sizes (248px / 72px).
        // It must NOT be position:fixed — that removes it from the grid and lets it float
        // over the main content column (which would then collapse/hide). Sticky + h-screen
        // keeps it pinned while the main column scrolls. Hidden below md (single-column).
        'sticky top-0 z-30 hidden h-screen w-full flex-col border-r border-[var(--omni-border)] md:flex',
        'bg-[var(--omni-bg-sidebar)]',
      )}
    >
      {/* Brand */}
      <div className={cn('flex h-[60px] shrink-0 items-center', collapsed ? 'px-0 justify-center' : 'px-4')}>
        <BrandLogo collapsed={collapsed} />
      </div>

      <div className="divider-x mx-3" />

      {/* Nav */}
      <ScrollArea className="flex-1 scroll-thin">
        <nav className={cn('flex flex-col gap-5 py-4', collapsed ? 'items-center px-3' : 'px-3')}>
          {navGroups.map((group, gi) => (
            <div
              key={group.label ?? `group-${gi}`}
              className={cn('flex flex-col gap-1', collapsed && 'w-full items-center')}
            >
              {group.label && !collapsed && (
                <span className="section-label px-3 pb-1">{group.label}</span>
              )}
              {group.items.map((item) => (
                <NavRow
                  key={item.to}
                  item={
                    item.to === '/approvals' && awaitingCount > 0
                      ? { ...item, badge: awaitingCount }  // live count, only when there are real approvals
                      : item
                  }
                  active={isActivePath(pathname, item.to)}
                  collapsed={collapsed}
                />
              ))}
            </div>
          ))}
        </nav>
      </ScrollArea>

      <div className="divider-x mx-3" />

      {/* Pinned user / plan card */}
      <div className={cn('shrink-0 p-3')}>
        {collapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="nav-item flex h-10 w-10 items-center justify-center px-0"
                aria-label="Omnivra AI — Enterprise Plan"
              >
                <Avatar className="h-8 w-8">
                  <AvatarImage src="" alt="Omnivra AI" />
                  <AvatarFallback className="tile-violet text-omnivra-purple">OA</AvatarFallback>
                </Avatar>
              </button>
            </TooltipTrigger>
            <TooltipContent side="right">Omnivra AI · Enterprise Plan</TooltipContent>
          </Tooltip>
        ) : (
          <div className="glass-card p-3">
            <div className="flex items-center gap-3">
              <Avatar className="h-9 w-9">
                <AvatarImage src="" alt="Omnivra AI" />
                <AvatarFallback className="tile-violet text-omnivra-purple">OA</AvatarFallback>
              </Avatar>
              <div className="flex min-w-0 flex-1 flex-col leading-tight">
                <span className="truncate text-sm font-semibold text-white">Omnivra AI</span>
                <span className="truncate text-xs text-[var(--omni-text-muted)]">
                  Enterprise Plan
                </span>
              </div>
              <NeonBadge tone="violet" className="shrink-0">
                Pro
              </NeonBadge>
            </div>

            <div className="mt-3 flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <span className="section-label normal-case tracking-normal">Storage</span>
                <span className="tabular text-xs font-medium text-[var(--omni-text-muted)]">68%</span>
              </div>
              <ProgressBar value={68} accent="violet" />
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
