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
  toggleSidebar: () => void
  setSidebarCollapsed: (v: boolean) => void
  setCommandOpen: (v: boolean) => void
  toggleRightRail: () => void
  setRealtimeStatus: (s: RealtimeStatus) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  commandOpen: false,
  rightRailOpen: true,
  realtimeStatus: 'idle',
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
  setCommandOpen: (v) => set({ commandOpen: v }),
  toggleRightRail: () => set((s) => ({ rightRailOpen: !s.rightRailOpen })),
  setRealtimeStatus: (s) => set({ realtimeStatus: s }),
}))
