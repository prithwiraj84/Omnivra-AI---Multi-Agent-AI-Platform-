import { useQuery } from '@tanstack/react-query'
import { Activity, KeyRound, Radio, ShieldCheck } from 'lucide-react'
import type { ReactNode } from 'react'

import { GlassCard } from '@/components/ui/glass-card'
import { NeonBadge } from '@/components/ui/neon-badge'
import { SectionHeader } from '@/components/ui/section-header'
import { StatusDot } from '@/components/ui/status-dot'
import { useAuthConfig } from '@/hooks/useAuth'
import { useSystemInfo } from '@/hooks/useSystem'
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
  const { data: info } = useSystemInfo()
  const realtimeStatus = useUIStore((s) => s.realtimeStatus)

  // Two independent gates: per-user Supabase workspaces and the legacy bearer token. Either one
  // means the app requires a sign-in, so report the effective state rather than just AUTH_ENABLED.
  const authEnabled = authConfig?.authEnabled ?? false
  const perUser = info?.perUserWorkspaces ?? false
  const signInRequired = perUser || authEnabled
  const realtime = REALTIME_VIEW[realtimeStatus]

  return (
    <div className="flex flex-col gap-6">
      <SectionHeader label="Settings" />

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
        {/* App health */}
        <GlassCard padding="md" className="flex h-full flex-col">
          <div className="flex flex-1 flex-col gap-4">
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
              <p className="flex flex-1 items-center justify-center text-sm text-[#71717a]">
                {healthError ? 'Backend unavailable.' : 'Loading…'}
              </p>
            )}
          </div>
        </GlassCard>

        {/* Auth mode — reports the EFFECTIVE sign-in requirement. Two independent gates exist:
            per-user Supabase workspaces (PER_USER_WORKSPACES) and the legacy bearer token
            (AUTH_ENABLED); either one means a login is required. */}
        <GlassCard padding="md" className="h-full">
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2.5">
              {signInRequired ? (
                <ShieldCheck className="h-4 w-4 text-omnivra-emerald" aria-hidden />
              ) : (
                <KeyRound className="h-4 w-4 text-omnivra-amber" aria-hidden />
              )}
              <span className="section-label">Authentication</span>
            </div>
            <div className="divide-y divide-white/5">
              <Row label="Mode">
                <NeonBadge tone={signInRequired ? 'success' : 'warning'} dot>
                  {perUser ? 'Per-user' : authEnabled ? 'Enabled' : 'Open'}
                </NeonBadge>
              </Row>
              <Row label="Access">
                {signInRequired ? 'Sign-in required' : 'No login required'}
              </Row>
              {perUser && <Row label="Workspaces">Private per user</Row>}
            </div>
            <p className="text-xs leading-relaxed text-[#a1a1aa]">
              {perUser
                ? 'Each signed-in user gets their own private projects; requests are verified against your Supabase project.'
                : authEnabled
                  ? 'A bearer token is required for protected actions.'
                  : 'Open mode — the app runs without sign-in. Set PER_USER_WORKSPACES=true (Supabase sign-in, private workspaces) or AUTH_ENABLED=true (single admin login).'}
            </p>
          </div>
        </GlassCard>

        {/* Realtime */}
        <GlassCard padding="md" className="h-full">
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
