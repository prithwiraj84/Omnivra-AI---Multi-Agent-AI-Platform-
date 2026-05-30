import { Activity, Gauge, ShieldCheck, Users } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge } from '@/components/ui/neon-badge'
import { StatusDot } from '@/components/ui/status-dot'
import { IconTile } from '@/components/ui/icon-tile'
import { ProgressBar } from '@/components/ui/progress-bar'
import { EmptyState } from '@/components/ui/empty-state'
import { AgentCard } from '@/components/dashboard/agent-card'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { AGENTS } from '@/config/agents'
import { useDashboard } from '@/hooks/useDashboard'
import type { Accent, ActivityItem, HealthMetric } from '@/types'

/** Higher utilization is worse: green under 70, amber 70–89, red at/above 90. */
function quotaAccent(pct: number): Accent {
  if (pct >= 90) return 'pink'
  if (pct >= 70) return 'amber'
  return 'emerald'
}

/** One quota row: label + a value-tinted ProgressBar with its display string. */
function QuotaRow({ metric }: { metric: HealthMetric }) {
  const value = metric.pct ?? 0
  const accent = quotaAccent(value)
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-3">
        <span className="truncate text-sm text-[#e4e4e7]">{metric.label}</span>
        <span className="tabular shrink-0 text-xs font-medium text-[#a1a1aa]">{metric.display}</span>
      </div>
      <ProgressBar value={value} accent={accent} />
    </div>
  )
}

/** One activity row: tinted IconTile + agent name, action and a relative timestamp. */
function ActivityRow({ item }: { item: ActivityItem }) {
  const Icon = item.icon
  return (
    <div className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
      <IconTile accent={item.accent} size="sm" icon={Icon} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-[#e4e4e7]">{item.agent}</p>
        <p className="truncate text-xs text-[#71717a]">{item.action}</p>
      </div>
      <span className="shrink-0 text-xs tabular text-[#71717a]">{item.time}</span>
    </div>
  )
}

/**
 * SecurityCenter — the Quality & Security department center (DESIGN_SYSTEM 8.3).
 * Renders the QA/SecOps agent roster, a "Security Posture" summary, the live API
 * quota gauges (from the dashboard systemHealth metrics labelled "API Quota …"),
 * and a stream of recent QA/SecOps activity. Reads dashboard data via useDashboard;
 * offline it renders the bundled fallback. Animated and reduced-motion safe.
 */
export function SecurityCenter() {
  const { data: dashboard } = useDashboard()

  const agents = AGENTS.filter((a) => a.department === 'Quality & Security')

  const quotas = (dashboard?.systemHealth ?? []).filter((m) => m.label.startsWith('API Quota'))

  const securityActivity = (dashboard?.activity ?? []).filter(
    (item) => item.agent.includes('SecOps') || item.agent.includes('QA'),
  )

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <GlassCard padding="md" glow="emerald" className="flex flex-col gap-3">
          <SectionHeader
            label="Security Center"
            count={agents.length}
            action={<NeonBadge tone="success">Quality &amp; Security</NeonBadge>}
          />
          <p className="max-w-prose text-sm leading-relaxed text-[#a1a1aa]">
            Verification and hardening. QA and SecOps engineers test every build and scan it for
            vulnerabilities before it ships.
          </p>
        </GlassCard>
      </Reveal>

      {agents.length === 0 ? (
        <GlassCard padding="none" className="overflow-hidden">
          <EmptyState
            icon={Users}
            title="No security agents"
            hint="The Quality & Security department has no registered agents yet."
            className="py-16"
          />
        </GlassCard>
      ) : (
        <Stagger className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5">
          {agents.map((agent) => (
            <StaggerItem key={agent.id}>
              <AgentCard agent={agent} />
            </StaggerItem>
          ))}
        </Stagger>
      )}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Reveal delay={0.05}>
          <GlassCard padding="md" className="flex h-full flex-col gap-4">
            <SectionHeader label="Security Posture" />
            <div className="flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2">
                <StatusDot status="online" pulse label="Secure" />
              </span>
              <NeonBadge tone="success" dot>
                0 Critical Errors / 24h
              </NeonBadge>
            </div>
            <div className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
              <IconTile accent="emerald" size="sm" icon={ShieldCheck} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-[#e4e4e7]">Last scan: passed</p>
                <p className="truncate text-xs text-[#71717a]">No vulnerabilities detected</p>
              </div>
            </div>
          </GlassCard>
        </Reveal>

        <Reveal delay={0.1}>
          <GlassCard padding="md" className="flex h-full flex-col gap-4">
            <SectionHeader label="API Quotas" count={quotas.length} />
            {quotas.length === 0 ? (
              <EmptyState
                icon={Gauge}
                title="No quota data"
                hint="Provider quota usage appears here once the dashboard reports it."
                className="py-10"
              />
            ) : (
              <Stagger className="flex flex-col gap-3.5">
                {quotas.map((metric) => (
                  <StaggerItem key={metric.label}>
                    <QuotaRow metric={metric} />
                  </StaggerItem>
                ))}
              </Stagger>
            )}
          </GlassCard>
        </Reveal>
      </div>

      <Reveal delay={0.15}>
        <GlassCard padding="md" className="flex flex-col gap-4">
          <SectionHeader label="Recent Security Activity" count={securityActivity.length} />
          {securityActivity.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="No security activity yet"
              hint="QA and SecOps actions appear here as workflows run."
              className="py-10"
            />
          ) : (
            <Stagger className="flex flex-col gap-2">
              {securityActivity.map((item) => (
                <StaggerItem key={item.id}>
                  <ActivityRow item={item} />
                </StaggerItem>
              ))}
            </Stagger>
          )}
        </GlassCard>
      </Reveal>
    </div>
  )
}
