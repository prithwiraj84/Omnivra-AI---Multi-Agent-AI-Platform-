/**
 * Department agent card + detail drawer (cp-0048). DeptAgentGrid renders the upgraded
 * cards (live status, model, call count, last activity) and opens a modal drawer with the
 * agent's full detail (provider/model, usage, responsibilities) on click.
 */
import { useEffect, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { Bot, X, Zap } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { IconTile } from '@/components/ui/icon-tile'
import { StatusDot, type DotStatus } from '@/components/ui/status-dot'
import { NeonBadge } from '@/components/ui/neon-badge'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import { cn } from '@/lib/utils'
import type { Accent } from '@/types'
import type { DeptAgent } from '@/lib/api/types'

const STATUS_LABEL: Record<string, string> = { working: 'Working', needs_approval: 'Needs approval', idle: 'Idle' }

function timeAgo(iso: string | null): string {
  if (!iso) return 'never'
  const secs = (Date.now() - new Date(iso).getTime()) / 1000
  if (Number.isNaN(secs)) return 'recently'
  if (secs < 60) return 'just now'
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`
  return `${Math.floor(secs / 86400)}d ago`
}

function DeptAgentCard({ agent, onOpen }: { agent: DeptAgent; onOpen: () => void }) {
  const reduce = useReducedMotion()
  const status = (agent.status as DotStatus) ?? 'idle'
  return (
    <motion.button
      type="button"
      onClick={onOpen}
      whileHover={reduce ? undefined : { scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 320, damping: 26 }}
      className="focus-ring w-full text-left"
    >
      <GlassCard interactive glow={agent.accent as Accent} padding="sm" className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <IconTile accent={agent.accent as Accent} size="sm" icon={Bot} />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium leading-snug text-zinc-100">{agent.name}</p>
            <p className="mt-0.5 break-words text-xs leading-snug text-zinc-500">{agent.modelLabel}</p>
          </div>
        </div>
        <div className="flex items-center justify-between border-t border-white/[0.06] pt-2.5">
          <StatusDot status={status} pulse={status !== 'idle'} label={STATUS_LABEL[agent.status] ?? 'Idle'} />
          <span className="tabular inline-flex items-center gap-1 text-[11px] text-[#71717a]">
            <Zap className="h-3 w-3" aria-hidden />
            {agent.calls}
          </span>
        </div>
      </GlassCard>
    </motion.button>
  )
}

function DeptAgentDrawer({ agent, onClose }: { agent: DeptAgent; onClose: () => void }) {
  const reduce = useReducedMotion()
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const status = (agent.status as DotStatus) ?? 'idle'
  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      initial={reduce ? undefined : { opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={reduce ? undefined : { opacity: 0 }}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-label={`${agent.name} detail`}
        initial={reduce ? undefined : { opacity: 0, scale: 0.96, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={reduce ? undefined : { opacity: 0, scale: 0.97 }}
        transition={{ type: 'spring', stiffness: 300, damping: 28 }}
        className="relative z-10 w-full max-w-md"
      >
        <GlassCard glow={agent.accent as Accent} padding="md" className="flex flex-col gap-4">
          <div className="flex items-start gap-3">
            <IconTile accent={agent.accent as Accent} size="md" icon={Bot} />
            <div className="min-w-0 flex-1">
              <p className="text-base font-semibold text-white">{agent.name}</p>
              <p className="text-xs text-[#a1a1aa]">{agent.modelLabel} · {agent.provider}</p>
            </div>
            <button type="button" onClick={onClose} aria-label="Close" className="focus-ring rounded-md p-1 text-[#a1a1aa] hover:text-white">
              <X className="h-4 w-4" aria-hidden />
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center">
            {[
              { label: 'Status', node: <StatusDot status={status} pulse={status !== 'idle'} label={STATUS_LABEL[agent.status] ?? 'Idle'} /> },
              { label: 'LLM Calls', node: <span className="tabular text-sm font-semibold text-white">{agent.calls}</span> },
              { label: 'Last active', node: <span className="text-xs text-[#d4d4d8]">{timeAgo(agent.lastActivity)}</span> },
            ].map((m) => (
              <div key={m.label} className="flex flex-col items-center gap-1 rounded-lg border border-white/[0.06] bg-white/[0.02] p-2.5">
                <span className="section-label">{m.label}</span>
                {m.node}
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="section-label">Model</span>
            <code className="rounded-md border border-white/[0.06] bg-white/[0.02] px-2.5 py-1.5 text-[11px] text-[#d4d4d8]">{agent.model}</code>
          </div>

          {agent.responsibilities.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <span className="section-label">Responsibilities</span>
              <div className="flex flex-wrap gap-1.5">
                {agent.responsibilities.map((r) => (
                  <NeonBadge key={r} tone="info">{r}</NeonBadge>
                ))}
              </div>
            </div>
          )}
        </GlassCard>
      </motion.div>
    </motion.div>
  )
}

export function DeptAgentGrid({ agents }: { agents: DeptAgent[] }) {
  const [selected, setSelected] = useState<DeptAgent | null>(null)
  return (
    <>
      {/* Wider cards (2 cols, 3 on very wide screens) so the agent name + model fit cleanly —
          the dept main column already shares space with the side panel + right rail. */}
      <Stagger className={cn('grid grid-cols-1 gap-3 sm:grid-cols-2 2xl:grid-cols-3')}>
        {agents.map((a) => (
          <StaggerItem key={a.id}>
            <DeptAgentCard agent={a} onOpen={() => setSelected(a)} />
          </StaggerItem>
        ))}
      </Stagger>
      <AnimatePresence>
        {selected && <DeptAgentDrawer agent={selected} onClose={() => setSelected(null)} />}
      </AnimatePresence>
    </>
  )
}
