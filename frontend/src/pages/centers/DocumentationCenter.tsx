import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, BookOpen, FileText, History, Presentation } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { ScrollArea } from '@/components/ui/scroll-area'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { EmptyState } from '@/components/ui/empty-state'
import { IconTile } from '@/components/ui/icon-tile'
import { AgentCard } from '@/components/dashboard/agent-card'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { AGENTS } from '@/config/agents'
import { useArtifacts } from '@/hooks/useArtifacts'
import { useDashboard } from '@/hooks/useDashboard'
import type { Artifact } from '@/lib/api/types'
import type { ActivityItem } from '@/types'

/** The artifact categories surfaced in the Documentation center. */
const DOC_CATEGORIES = ['docs', 'presentations'] as const

/** Per-category presentation: NeonBadge tone for the category pill. */
const CATEGORY_TONE: Record<string, BadgeTone> = {
  docs: 'cyan',
  presentations: 'warning',
}

/** Format an ISO timestamp into a compact local "MMM d, HH:mm" — falls back to the raw string. */
function formatModified(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** One docs/decks row: a category IconTile, the path + modified time, and a category badge. */
function DocRow({ artifact }: { artifact: Artifact }) {
  const isDeck = artifact.category === 'presentations'
  return (
    <div className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
      <IconTile
        accent={isDeck ? 'pink' : 'cyan'}
        size="sm"
        icon={isDeck ? Presentation : FileText}
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-[#e4e4e7]">{artifact.path}</p>
        <p className="truncate text-xs text-[#71717a]">{formatModified(artifact.modified)}</p>
      </div>
      <NeonBadge tone={CATEGORY_TONE[artifact.category] ?? 'info'} className="shrink-0 capitalize">
        {artifact.category}
      </NeonBadge>
    </div>
  )
}

/** One recent-documentation-activity row: agent name + action + relative time. */
function ActivityRow({ item }: { item: ActivityItem }) {
  return (
    <div className="flex items-start gap-3">
      <IconTile accent={item.accent} size="sm" icon={item.icon} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-zinc-200">{item.agent}</p>
        <p className="truncate text-xs text-zinc-400">{item.action}</p>
      </div>
      <span className="shrink-0 text-xs text-zinc-500">{item.time}</span>
    </div>
  )
}

/**
 * DocumentationCenter — the Documentation department detail panel (DESIGN_SYSTEM 8.3).
 * Header + the Documentation roster (AgentCard grid), a "Docs & Decks" panel listing
 * workspace artifacts in the {docs, presentations} categories (with a hint linking to
 * /documents), and a recent-documentation-activity feed filtered from the dashboard
 * activity stream. Offline (jsdom/tests) the artifact list is empty and the EmptyState
 * renders without crashing.
 */
export function DocumentationCenter() {
  const { data: artifacts } = useArtifacts()
  const dashboard = useDashboard()

  const agents = useMemo(() => AGENTS.filter((a) => a.department === 'Documentation'), [])

  const docs = useMemo(() => {
    const all = artifacts ?? []
    return all
      .filter((a) => (DOC_CATEGORIES as readonly string[]).includes(a.category))
      .sort((a, b) => b.modified.localeCompare(a.modified))
  }, [artifacts])

  const docActivity = useMemo(
    () => dashboard.data.activity.filter((a) => a.agent.includes('Documentation')),
    [dashboard.data.activity],
  )

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <GlassCard padding="md" glow="cyan" className="flex flex-col gap-3">
          <SectionHeader
            label="Documentation Center"
            count={agents.length}
            action={<NeonBadge tone="cyan">Department</NeonBadge>}
          />
          <p className="max-w-prose text-sm leading-relaxed text-[#a1a1aa]">
            Knowledge capture. Documentation and presentation agents keep the company
            explainable — turning every build into readable docs and polished decks.
          </p>
        </GlassCard>
      </Reveal>

      {agents.length === 0 ? (
        <GlassCard padding="none" className="overflow-hidden">
          <EmptyState
            icon={BookOpen}
            title="No documentation agents"
            hint="No agents are registered to the Documentation department yet."
            className="py-16"
          />
        </GlassCard>
      ) : (
        <Reveal delay={0.05}>
          <Stagger className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5">
            {agents.map((agent) => (
              <StaggerItem key={agent.id}>
                <AgentCard agent={agent} />
              </StaggerItem>
            ))}
          </Stagger>
        </Reveal>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Reveal delay={0.1}>
          <GlassCard padding="none" className="overflow-hidden">
            <div className="flex flex-col gap-2 border-b border-white/5 p-5">
              <SectionHeader
                label="Docs & Decks"
                count={docs.length}
                action={
                  <Link
                    to="/documents"
                    className="focus-ring inline-flex items-center gap-1 rounded-md text-xs font-medium text-omnivra-cyan transition-colors hover:brightness-110"
                  >
                    Open Documents
                    <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
                  </Link>
                }
              />
            </div>

            {docs.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="No docs or decks yet"
                hint="Run a documentation workflow — generated docs and presentations land here. Browse them in Documents."
                className="py-14"
              />
            ) : (
              <ScrollArea className="max-h-[30rem]">
                <Stagger className="flex flex-col gap-2 p-4">
                  {docs.map((artifact) => (
                    <StaggerItem key={artifact.path}>
                      <DocRow artifact={artifact} />
                    </StaggerItem>
                  ))}
                </Stagger>
              </ScrollArea>
            )}
          </GlassCard>
        </Reveal>

        <Reveal delay={0.15}>
          <GlassCard padding="none" className="overflow-hidden">
            <div className="border-b border-white/5 p-5">
              <SectionHeader label="Recent Documentation Activity" count={docActivity.length} />
            </div>

            {docActivity.length === 0 ? (
              <EmptyState
                icon={History}
                title="No documentation activity"
                hint="Documentation agent actions appear here as workflows run."
                className="py-14"
              />
            ) : (
              <ScrollArea className="max-h-[30rem]">
                <Stagger className="flex flex-col gap-2.5 p-4">
                  {docActivity.map((item) => (
                    <StaggerItem key={item.id}>
                      <ActivityRow item={item} />
                    </StaggerItem>
                  ))}
                </Stagger>
              </ScrollArea>
            )}
          </GlassCard>
        </Reveal>
      </div>
    </div>
  )
}
