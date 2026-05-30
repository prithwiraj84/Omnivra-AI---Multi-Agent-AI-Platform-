/**
 * Realtime WebSocket event helpers.
 *
 * The backend streams camelCase JSON frames over /ws (see backend/app/schemas/events.py:
 * Event{type, payload, ts}). These helpers adapt the wire payloads into the icon-resolved
 * domain shapes the dashboard consumes — mirroring the GET /api/dashboard adapter
 * (./dashboard), but for the live push channel.
 */
import { resolveIcon } from '@/lib/api/icons'
import type { ActivityDTO } from '@/lib/api/types'
import type { ActivityItem, HealthMetric } from '@/types'

/** Raw frame as it arrives on the wire. `payload` shape varies by `type`. */
export interface WsEvent {
  type: string
  payload: unknown
  ts: string
}

/** Wire shape of a 'system_health' payload. */
export interface HealthPayload {
  metrics: HealthMetric[]
}

/**
 * Map an 'activity' payload (a single ActivityItem with a string `icon` key) into the
 * UI shape, resolving the icon key to a Lucide component.
 */
export function activityFromEvent(payload: ActivityDTO): ActivityItem {
  return {
    id: String(payload.id),
    agent: payload.agent,
    action: payload.action,
    time: payload.time,
    accent: payload.accent,
    icon: resolveIcon(payload.icon),
  }
}

/**
 * Map a 'system_health' payload into the HealthMetric[] the System Health panel reads.
 * HealthMetric carries no icon, so the metrics pass through unchanged.
 */
export function healthFromEvent(payload: HealthPayload): HealthMetric[] {
  return payload.metrics
}
