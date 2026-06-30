/**
 * useWebSocket — the single live data channel for the app.
 *
 * Connects to the backend /ws endpoint (Vite proxies /ws -> ws://localhost:8000) and
 * folds streamed events into the React Query ['dashboard'] cache so the dashboard
 * sections re-render in place:
 *   - 'system_health' -> replaces DashboardData.systemHealth
 *   - 'activity'       -> prepends a new ActivityItem (capped at 12)
 *   - 'workflow' / 'approval' -> prepend a synthesized activity line (best-effort)
 *   - 'hello'          -> ignored (handshake)
 *
 * Lifecycle is surfaced via useUIStore.realtimeStatus. jsdom has no WebSocket global,
 * so we short-circuit to 'unsupported' there (keeps the smoke test green). On close we
 * reconnect with a capped exponential backoff; the effect cleanup tears everything down.
 *
 * Mount this ONCE (AppLayout). The hook returns the current realtime status.
 */
import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useUIStore } from '@/store/ui'
import { useSocialProgressStore } from '@/store/social-progress'
import type { ActivityDTO, DashboardData, SocialProgressEvent } from '@/lib/api/types'
import {
  activityFromEvent,
  healthFromEvent,
  type HealthPayload,
  type WsEvent,
} from '@/lib/api/events'
import type { ActivityItem } from '@/types'

const ACTIVITY_CAP = 12
const MAX_BACKOFF_MS = 15_000
const BASE_BACKOFF_MS = 1_000

/** Prepend a new activity item to the cached feed, capped at ACTIVITY_CAP. */
function prependActivity(old: DashboardData | undefined, item: ActivityItem) {
  if (!old) return old
  return { ...old, activity: [item, ...old.activity].slice(0, ACTIVITY_CAP) }
}

export function useWebSocket() {
  const queryClient = useQueryClient()
  const setRealtimeStatus = useUIStore((s) => s.setRealtimeStatus)
  const realtimeStatus = useUIStore((s) => s.realtimeStatus)

  useEffect(() => {
    // jsdom (and any non-browser host) has no WebSocket — no-op cleanly.
    if (typeof WebSocket === 'undefined') {
      setRealtimeStatus('unsupported')
      return
    }

    let socket: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let attempts = 0
    let disposed = false

    const handleMessage = (raw: string) => {
      let event: WsEvent
      try {
        event = JSON.parse(raw) as WsEvent
      } catch {
        return
      }
      const { type, payload } = event

      switch (type) {
        case 'system_health':
          queryClient.setQueryData<DashboardData>(['dashboard'], (old) =>
            old ? { ...old, systemHealth: healthFromEvent(payload as HealthPayload) } : old,
          )
          break
        case 'activity':
          queryClient.setQueryData<DashboardData>(['dashboard'], (old) =>
            prependActivity(old, activityFromEvent(payload as ActivityDTO)),
          )
          break
        case 'workflow':
        case 'approval': {
          // A workflow frame fires when a run starts, an agent picks up work, or it ends — refresh
          // the dashboard so the workflow card shows the live status (which agent is working) at once
          // instead of waiting for the next poll.
          queryClient.invalidateQueries({ queryKey: ['dashboard'] })
          // Best-effort: also surface it as a feed line when it carries an activity-shaped payload.
          const p = payload as Partial<ActivityDTO> | null
          if (p && p.id != null && (p.agent || p.action)) {
            queryClient.setQueryData<DashboardData>(['dashboard'], (old) =>
              prependActivity(old, activityFromEvent(payload as ActivityDTO)),
            )
          }
          break
        }
        case 'social_progress': {
          // Live per-step generation/render progress -> the Social Studio store.
          const p = payload as SocialProgressEvent | null
          if (p && p.jobId) {
            useSocialProgressStore.getState().upsert(p, Date.now())
            // A terminal render frame isn't reflected in draft.renderStatus until the next
            // 10s poll — refresh now so the reel card swaps to the player / Re-render promptly.
            if (p.phase === 'render' && (p.step === 'rendered' || p.status === 'error')) {
              queryClient.invalidateQueries({ queryKey: ['social'] })
            }
          }
          break
        }
        case 'hello':
        default:
          break
      }
    }

    const scheduleReconnect = () => {
      if (disposed) return
      const delay = Math.min(BASE_BACKOFF_MS * 2 ** attempts, MAX_BACKOFF_MS)
      attempts += 1
      reconnectTimer = setTimeout(connect, delay)
    }

    function connect() {
      if (disposed) return
      setRealtimeStatus('connecting')

      // Prod (Vercel -> remote backend): VITE_WS_URL points at the backend's wss .../ws. Dev: same
      // origin (Vite proxies /ws -> ws://localhost:8000).
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      const url = import.meta.env.VITE_WS_URL || `${proto}://${location.host}/ws`

      try {
        socket = new WebSocket(url)
      } catch {
        scheduleReconnect()
        return
      }

      socket.onopen = () => {
        attempts = 0
        setRealtimeStatus('open')
      }
      socket.onmessage = (ev) => handleMessage(String(ev.data))
      socket.onerror = () => {
        // Surface as closed; the close handler drives reconnect.
        setRealtimeStatus('closed')
      }
      socket.onclose = () => {
        setRealtimeStatus('closed')
        socket = null
        scheduleReconnect()
      }
    }

    connect()

    return () => {
      disposed = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (socket) {
        socket.onopen = null
        socket.onmessage = null
        socket.onerror = null
        socket.onclose = null
        socket.close()
        socket = null
      }
    }
    // queryClient + the setter are stable; we intentionally connect once per mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return realtimeStatus
}
