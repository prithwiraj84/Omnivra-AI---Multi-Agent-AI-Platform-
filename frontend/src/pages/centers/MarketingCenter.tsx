import { Activity, FileText, Megaphone, Users } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { IconTile } from '@/components/ui/icon-tile'
import { ProgressBar } from '@/components/ui/progress-bar'
import { EmptyState } from '@/components/ui/empty-state'
import { AgentCard } from '@/components/dashboard/agent-card'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { AGENTS } from '@/config/agents'
import { useDashboard } from '@/hooks/useDashboard'
import { useArtifacts } from '@/hooks/useArtifacts'
import type { Artifact } from '@/lib/api/types'
import type { ActivityItem, WorkflowItem, WorkflowStatus } from '@/types'

/** Workflow lifecycle status → NeonBadge tone. */
const STATUS_TONE: Record<WorkflowStatus, BadgeTone> = {
  'In Progress': 'info',
  Review: 'warning',
  Completed: 'success',
  Failed: 'danger',
  Queued: 'cyan',
}

/** Format an ISO-ish timestamp for display; falls back to the raw string. */
function formatModified(modified: string): string {
  const date = new Date(modified)
  if (Number.isNaN(date.getTime())) return modified
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** One campaign row: workflow name + status badge + a progress bar. */
function CampaignRow({ workflow }: { workflow: WorkflowItem }) {
  const Icon = workflow.icon
  return (
    <div className="flex flex-col gap-2.5 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3.5">
      <div className="flex items-center gap-3">
        <IconTile accent={workflow.accent} size="sm" icon={Icon} />
        <p className="min-w-0 flex-1 truncate text-sm font-medium text-[#e4e4e7]">{workflow.name}</p>
        <NeonBadge tone={STATUS_TONE[workflow.status]}>{workflow.status}</NeonBadge>
      </div>
      <ProgressBar value={workflow.progress} accent={workflow.accent} />
    </div>
  )
}

/** One artifact row: file path + modified time, with a link hint to the workspace. */
function ArtifactRow({ artifact }: { artifact: Artifact }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
      <IconTile accent="violet" size="sm" icon={FileText} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-[#e4e4e7]">{artifact.path}</p>
        <p className="truncate text-xs text-[#71717a]">
          {formatModified(artifact.modified)} · open in /workspace
        </p>
      </div>
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

/** Roster names of the Marketing department, used to scope recent activity. */
const MARKETING_AGENT_NAMES = new Set(
  AGENTS.filter((a) => a.department === 'Marketing').map((a) => a.name),
)

/**
 * MarketingCenter — the Marketing department center (DESIGN_SYSTEM 8.3). Renders
 * the Marketing agent roster, live campaigns (dashboard workflows scoped to the
 * Marketing department), report artifacts written to the workspace, and recent
 * marketing activity. Dashboard data via useDashboard, artifacts via useArtifacts;
 * both fall back gracefully offline. Animated and reduced-motion safe.
 */
export function MarketingCenter() {
  const { data: dashboard } = useDashboard()
  const { data: artifactList } = useArtifacts()

  const agents = AGENTS.filter((a) => a.department === 'Marketing')

  const campaigns = (dashboard?.workflows ?? []).filter((w) => w.department === 'Marketing')

  const reports = (artifactList ?? []).filter((a) => a.category === 'reports')

  const marketingActivity = (dashboard?.activity ?? []).filter((item) =>
    MARKETING_AGENT_NAMES.has(item.agent),
  )

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <GlassCard padding="md" glow="cyan" className="flex flex-col gap-3">
          <SectionHeader
            label="Marketing Center"
            count={agents.length}
            action={<NeonBadge tone="cyan">Marketing</NeonBadge>}
          />
          <p className="max-w-prose text-sm leading-relaxed text-[#a1a1aa]">
            Reach and growth. SEO, social and reel-automation agents take the product to its
            audience and track every campaign.
          </p>
        </GlassCard>
      </Reveal>

      {agents.length === 0 ? (
        <GlassCard padding="none" className="overflow-hidden">
          <EmptyState
            icon={Users}
            title="No marketing agents"
            hint="The Marketing department has no registered agents yet."
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
            <SectionHeader label="Campaigns" count={campaigns.length} />
            {campaigns.length === 0 ? (
              <EmptyState
                icon={Megaphone}
                title="No active campaigns"
                hint="Marketing workflows appear here as the team launches them."
                className="py-10"
              />
            ) : (
              <Stagger className="flex flex-col gap-2.5">
                {campaigns.map((workflow) => (
                  <StaggerItem key={workflow.id}>
                    <CampaignRow workflow={workflow} />
                  </StaggerItem>
                ))}
              </Stagger>
            )}
          </GlassCard>
        </Reveal>

        <Reveal delay={0.1}>
          <GlassCard padding="md" className="flex h-full flex-col gap-4">
            <SectionHeader label="Content Artifacts" count={reports.length} />
            {reports.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="No content artifacts yet"
                hint="Reports written to the workspace appear here. Run a marketing workflow to populate it."
                className="py-10"
              />
            ) : (
              <Stagger className="flex flex-col gap-2">
                {reports.map((artifact) => (
                  <StaggerItem key={artifact.path}>
                    <ArtifactRow artifact={artifact} />
                  </StaggerItem>
                ))}
              </Stagger>
            )}
          </GlassCard>
        </Reveal>
      </div>

      <Reveal delay={0.15}>
        <GlassCard padding="md" className="flex flex-col gap-4">
          <SectionHeader label="Recent Marketing Activity" count={marketingActivity.length} />
          {marketingActivity.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="No marketing activity yet"
              hint="SEO, social and reel-automation actions appear here as workflows run."
              className="py-10"
            />
          ) : (
            <Stagger className="flex flex-col gap-2">
              {marketingActivity.map((item) => (
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
