import { Outlet, useLocation } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'

import { cn } from '@/lib/utils'
import { pageTransition } from '@/lib/motion'
import { useUIStore } from '@/store/ui'
import { useWebSocket } from '@/hooks/useWebSocket'

import { RightRail } from './right-rail'
import { Sidebar } from './sidebar'
import { Topbar } from './topbar'

/**
 * AppLayout — the persistent page chrome.
 *
 * CSS grid with three tracks: [Sidebar | main | RightRail].
 *  - Sidebar width tracks `useUIStore.sidebarCollapsed` (248px expanded / 72px rail).
 *  - RightRail is a fixed 320px track, hidden below the `xl` breakpoint and whenever
 *    `useUIStore.rightRailOpen` is false (collapses to a 0px track so the main column reflows).
 *  - The main column stacks a sticky <Topbar /> over a scrollable content region that renders
 *    the routed <Outlet /> (max-width ~1600px, p-6 gutter, centered).
 *
 * The whole app sits on `--omni-bg-base` with a faint blueprint grid + an ambient glow behind
 * the top. Grid-column transitions keep sidebar/rail toggles smooth.
 */
export function AppLayout() {
  // The single live /ws connection for the whole app (folds events into the
  // ['dashboard'] query cache). Mounted here so it spans every route.
  useWebSocket()

  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed)
  const rightRailOpen = useUIStore((s) => s.rightRailOpen)

  // Re-trigger a fade+rise on the content region whenever the route changes.
  const { pathname } = useLocation()
  const reduce = useReducedMotion()

  return (
    <div
      className="relative h-screen w-full overflow-hidden"
      style={{ backgroundColor: 'var(--omni-bg-base)' }}
    >
      {/* Faint blueprint grid wash across the whole surface */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 bg-grid-faint [background-size:32px_32px] opacity-60"
      />
      {/* Ambient neon glow anchored behind the top of the app */}
      <div
        aria-hidden
        className="ambient-glow pointer-events-none fixed inset-x-0 top-0 h-[420px]"
      />

      {/* Three-track shell. Columns animate when the sidebar/rail toggle. */}
      <div
        className={cn(
          'relative z-10 grid h-screen w-full',
          'transition-[grid-template-columns] duration-300 ease-out-quint',
          // mobile: single column (sidebar handles its own off-canvas behaviour)
          'grid-cols-1',
          // md+: [sidebar | main]
          sidebarCollapsed
            ? 'md:grid-cols-[72px_minmax(0,1fr)]'
            : 'md:grid-cols-[248px_minmax(0,1fr)]',
          // xl: add the right-rail track (0px when closed so the main column expands)
          rightRailOpen
            ? sidebarCollapsed
              ? 'xl:grid-cols-[72px_minmax(0,1fr)_320px]'
              : 'xl:grid-cols-[248px_minmax(0,1fr)_320px]'
            : sidebarCollapsed
              ? 'xl:grid-cols-[72px_minmax(0,1fr)_0px]'
              : 'xl:grid-cols-[248px_minmax(0,1fr)_0px]',
        )}
      >
        {/* Column 1 — Sidebar (sticky, full height) */}
        <Sidebar />

        {/* Column 2 — main: fixed Topbar over its OWN scrollable content region. h-screen +
            min-h-0 so the <main> overflow-y-auto scrolls independently (not the whole page). */}
        <div className="flex h-screen min-h-0 min-w-0 flex-col">
          <Topbar />

          <main className="scroll-thin min-h-0 flex-1 overflow-y-auto">
            <div className="mx-auto w-full max-w-[1600px] p-6">
              {reduce ? (
                <div>
                  <Outlet />
                </div>
              ) : (
                <motion.div
                  key={pathname}
                  variants={pageTransition}
                  initial="hidden"
                  animate="show"
                >
                  <Outlet />
                </motion.div>
              )}
            </div>
          </main>
        </div>

        {/* Column 3 — RightRail (xl+ only, fixed 320px track). h-screen so its content sits within
            the viewport — the rail's fixed set of cards fits without scrolling on a normal screen
            (and only scrolls internally on a very short viewport). */}
        <div
          className={cn(
            'hidden h-screen overflow-hidden',
            rightRailOpen && 'xl:block',
          )}
        >
          <RightRail />
        </div>
      </div>
    </div>
  )
}
