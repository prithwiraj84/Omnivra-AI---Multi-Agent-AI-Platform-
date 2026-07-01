import { useQuery } from '@tanstack/react-query'
import { Activity, KeyRound, Radio, ShieldCheck } from 'lucide-react'
import type { ReactNode } from 'react'

import { GlassCard } from '@/components/ui/glass-card'
import { NeonBadge } from '@/components/ui/neon-badge'
import { SectionHeader } from '@/components/ui/section-header'
import { StatusDot } from '@/components/ui/status-dot'
import { useAuthConfig } from '@/hooks/useAuth'
import { backendOrigin } from '@/lib/api/client'
import { useUIStore, type RealtimeStatus } from '@/store/ui'

/** Liveness/summary shape from GET /health (served at the app root, not under /api). */
interface HealthInfo {
  status: string
  app: string
  version: string
  env: string
  agents: number
}

/** Fetch GET /health directly (it lives at the root, outside the /api axios baseURL). */
async function fetchHealth(): Promise<HealthInfo> {
  const res = await fetch(`${backendOrigin}/health`)
  if (!res.ok) throw new Error(`health ${res.status}`)
  return (await res.json()) as HealthInfo
}

/** App liveness/summary. Single retry so an offline host settles quickly. */
function useHealth() {
  return useQuery<HealthInfo>({
    queryKey: ['health'],
    queryFn: fetchHealth,
    retry: 1,
    staleTime: 30_000,
  })
}

/** One label/value row inside a settings card. */
function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2">
      <span className="text-xs text-[#71717a]">{label}</span>
      <span className="text-right text-sm text-[#e4e4e7]">{children}</span>
    </div>
  )
}

/** Tone + dot status + copy for each realtime channel state. */
const REALTIME_VIEW: Record<
  RealtimeStatus,
  { label: string; tone: 'success' | 'warning' | 'danger' | 'info'; dot: 'online' | 'busy' | 'offline' | 'idle' }
> = {
  open: { label: 'Connected', tone: 'success', dot: 'online' },
  connecting: { label: 'Connecting', tone: 'warning', dot: 'busy' },
  closed: { label: 'Disconnected', tone: 'danger', dot: 'offline' },
  unsupported: { label: 'Unsupported', tone: 'danger', dot: 'offline' },
  idle: { label: 'Idle', tone: 'info', dot: 'idle' },
}

/**
 * Settings — a read-only status page. Three on-brand GlassCards report the live
 * system state: app health (GET /health: status, version, env, agent count), the
 * Auth mode (Enabled / Open, from GET /auth/config) and the realtime channel status
 * (from the UI store). Everything degrades gracefully offline: health shows
 * "Unavailable", auth defaults to Open, realtime reflects whatever the socket reports.
 */
export function Settings() {
  const { data: health, isError: healthError } = useHealth()
  const { data: authConfig } = useAuthConfig()
  const realtimeStatus = useUIStore((s) => s.realtimeStatus)

  const authEnabled = authConfig?.authEnabled ?? false
  const realtime = REALTIME_VIEW[realtimeStatus]

  return (
    <div className="flex flex-col gap-6">
      <SectionHeader label="Settings" />

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
        {/* App health */}
        <GlassCard padding="md">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2.5">
              <Activity className="h-4 w-4 text-omnivra-cyan" aria-hidden />
              <span className="section-label">System Health</span>
            </div>
            {health ? (
              <div className="divide-y divide-white/5">
                <Row label="Status">
                  <NeonBadge tone="success" dot>
                    {health.status}
                  </NeonBadge>
                </Row>
                <Row label="Version">
                  <span className="font-mono">{health.version}</span>
                </Row>
                <Row label="Environment">
                  <span className="font-mono">{health.env}</span>
                </Row>
                <Row label="Registered agents">
                  <span className="tabular">{health.agents}</span>
                </Row>
              </div>
            ) : (
              <p className="text-sm text-[#71717a]">
                {healthError ? 'Backend unavailable.' : 'Loading…'}
              </p>
            )}
          </div>
        </GlassCard>

        {/* Auth mode */}
        <GlassCard padding="md">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2.5">
              {authEnabled ? (
                <ShieldCheck className="h-4 w-4 text-omnivra-emerald" aria-hidden />
              ) : (
                <KeyRound className="h-4 w-4 text-omnivra-amber" aria-hidden />
              )}
              <span className="section-label">Authentication</span>
            </div>
            <div className="divide-y divide-white/5">
              <Row label="Mode">
                <NeonBadge tone={authEnabled ? 'success' : 'warning'} dot>
                  {authEnabled ? 'Enabled' : 'Open'}
                </NeonBadge>
              </Row>
              <Row label="Access">
                {authEnabled ? 'Login required' : 'No login required'}
              </Row>
            </div>
            <p className="text-xs leading-relaxed text-[#71717a]">
              {authEnabled
                ? 'A bearer token is required for protected actions.'
                : 'Open mode — the app runs without sign-in. Set AUTH_ENABLED=true to require a login.'}
            </p>
          </div>
        </GlassCard>

        {/* Realtime */}
        <GlassCard padding="md">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2.5">
              <Radio className="h-4 w-4 text-omnivra-cyan" aria-hidden />
              <span className="section-label">Realtime Channel</span>
            </div>
            <div className="divide-y divide-white/5">
              <Row label="WebSocket">
                <NeonBadge tone={realtime.tone}>{realtime.label}</NeonBadge>
              </Row>
              <Row label="State">
                <StatusDot status={realtime.dot} label={realtimeStatus} />
              </Row>
            </div>
            <p className="text-xs leading-relaxed text-[#71717a]">
              The live channel streams activity, workflow progress and system-health updates.
            </p>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
