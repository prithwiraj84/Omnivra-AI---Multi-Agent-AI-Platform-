import { Brain, History, ScrollText, Sparkles } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { ScrollArea } from '@/components/ui/scroll-area'
import { EmptyState } from '@/components/ui/empty-state'
import { IconTile } from '@/components/ui/icon-tile'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { useDashboard } from '@/hooks/useDashboard'
import { useRecentMemory } from '@/hooks/useMemory'
import type { ActivityItem } from '@/types'

/** Read a string field from a metadata bag, falling back to `undefined`. */
function metaString(metadata: Record<string, unknown>, key: string): string | undefined {
  const value = metadata[key]
  return typeof value === 'string' && value.length > 0 ? value : undefined
}

/** Resolve the originating agent from a memory item's metadata. */
function agentOf(metadata: Record<string, unknown>): string | undefined {
  return metaString(metadata, 'agentId') ?? metaString(metadata, 'agent')
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
 * Logs — a read-only system activity log. The left panel lists recent agent
 * activity (IconTile + agent + action + time) from the dashboard payload; the
 * right panel lists the newest agent memory entries (each with the producing
 * agent from metadata). Both render inside a scrollable GlassCard with a
 * staggered entrance. Offline (jsdom/tests) the activity falls back to the
 * bundled dashboard data and the memory list renders its EmptyState.
 */
export function Logs() {
  const { data: dashboard } = useDashboard()
  const { data: memory } = useRecentMemory(12)

  const activity = dashboard?.activity ?? []
  const memoryItems = memory ?? []

  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <Reveal>
        <GlassCard padding="none" className="overflow-hidden">
          <div className="border-b border-white/5 p-5">
            <SectionHeader label="Activity Log" count={activity.length} />
          </div>
          {activity.length === 0 ? (
            <EmptyState
              icon={ScrollText}
              title="No activity yet"
              hint="Agent actions appear here as workflows run."
              className="py-16"
            />
          ) : (
            <ScrollArea className="max-h-[34rem]">
              <Stagger className="flex flex-col gap-2 p-4">
                {activity.map((item) => (
                  <StaggerItem key={item.id}>
                    <ActivityRow item={item} />
                  </StaggerItem>
                ))}
              </Stagger>
            </ScrollArea>
          )}
        </GlassCard>
      </Reveal>

      <Reveal delay={0.05}>
        <GlassCard padding="none" className="overflow-hidden">
          <div className="border-b border-white/5 p-5">
            <SectionHeader label="Recent Memory" count={memoryItems.length} />
          </div>
          {memoryItems.length === 0 ? (
            <EmptyState
              icon={Brain}
              title="No memory entries yet"
              hint="Each agent's output is stored as recall after a workflow run. Run one to populate this log."
              className="py-16"
            />
          ) : (
            <ScrollArea className="max-h-[34rem]">
              <Stagger className="flex flex-col gap-2 p-4">
                {memoryItems.map((entry) => {
                  const agent = agentOf(entry.metadata)
                  return (
                    <StaggerItem key={entry.id}>
                      <div className="flex flex-col gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3.5">
                        <p className="text-sm leading-relaxed text-[#e4e4e7]">{entry.text}</p>
                        <div className="flex items-center gap-1.5 text-xs text-[#71717a]">
                          {agent ? (
                            <>
                              <Sparkles className="h-3.5 w-3.5 shrink-0" aria-hidden />
                              <span className="truncate">{agent}</span>
                            </>
                          ) : (
                            <>
                              <History className="h-3.5 w-3.5 shrink-0" aria-hidden />
                              <span className="truncate">Memory entry</span>
                            </>
                          )}
                        </div>
                      </div>
                    </StaggerItem>
                  )
                })}
              </Stagger>
            </ScrollArea>
          )}
        </GlassCard>
      </Reveal>
    </div>
  )
}
