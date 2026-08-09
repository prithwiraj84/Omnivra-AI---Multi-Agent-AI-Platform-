/** Global UI state (Zustand). Layout chrome + command palette + density. */
import { create } from 'zustand'

/** Lifecycle of the live /ws connection (see hooks/useWebSocket). */
export type RealtimeStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'unsupported'

interface UIState {
  /** Sidebar collapsed to icon-rail width. */
  sidebarCollapsed: boolean
  /** Command palette (⌘K) open. */
  commandOpen: boolean
  /** Right rail visible (hidden on narrow viewports). */
  rightRailOpen: boolean
  /** Live WebSocket connection status (drives the topbar live indicator). */
  realtimeStatus: RealtimeStatus
  /** When the Error Log page was last opened (ms epoch) — the sidebar badge counts newer records. */
  errorsSeenAt: number
  toggleSidebar: () => void
  setSidebarCollapsed: (v: boolean) => void
  setCommandOpen: (v: boolean) => void
  toggleRightRail: () => void
  setRealtimeStatus: (s: RealtimeStatus) => void
  markErrorsSeen: () => void
}

// Persisted so a page refresh doesn't resurrect an already-dismissed badge.
const SEEN_KEY = 'omnivra.errorsSeenAt'
const initialSeen = (): number => {
  try {
    return Number(localStorage.getItem(SEEN_KEY)) || 0
  } catch {
    return 0
  }
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  commandOpen: false,
  rightRailOpen: true,
  realtimeStatus: 'idle',
  errorsSeenAt: initialSeen(),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
  setCommandOpen: (v) => set({ commandOpen: v }),
  toggleRightRail: () => set((s) => ({ rightRailOpen: !s.rightRailOpen })),
  setRealtimeStatus: (s) => set({ realtimeStatus: s }),
  markErrorsSeen: () => {
    const now = Date.now()
    try {
      localStorage.setItem(SEEN_KEY, String(now))
    } catch {
      /* private mode — session-only badge is fine */
    }
    set({ errorsSeenAt: now })
  },
}))
