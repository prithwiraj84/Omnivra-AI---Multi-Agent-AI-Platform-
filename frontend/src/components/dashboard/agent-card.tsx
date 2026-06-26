import {
  Bot,
  BookMarked,
  Code2,
  Compass,
  Cpu,
  Crown,
  LifeBuoy,
  Megaphone,
  Palette,
  ShieldCheck,
  Sparkles,
  type LucideIcon,
} from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import { GlassCard } from '@/components/ui/glass-card'
import { IconTile } from '@/components/ui/icon-tile'
import { StatusDot, type DotStatus } from '@/components/ui/status-dot'
import type { AgentStatus, AgentSummary } from '@/types'

/** Map the agent's live status (from the dashboard) to a presence dot + label + pulse. */
const STATUS_VIEW: Record<string, { dot: DotStatus; label: string; pulse: boolean }> = {
  working: { dot: 'working', label: 'Working', pulse: true },
  needs_approval: { dot: 'needs_approval', label: 'Needs approval', pulse: true },
  idle: { dot: 'idle', label: 'Idle', pulse: false },
  online: { dot: 'online', label: 'Online', pulse: true },
  busy: { dot: 'busy', label: 'Busy', pulse: true },
  offline: { dot: 'offline', label: 'Offline', pulse: false },
  error: { dot: 'offline', label: 'Error', pulse: false },
}

function statusView(status: AgentStatus) {
  return STATUS_VIEW[status] ?? STATUS_VIEW.idle
}

/** Department → glyph map for the agent tile icon. */
const DEPARTMENT_ICON: Record<string, LucideIcon> = {
  Executive: Crown,
  Architecture: Compass,
  Design: Palette,
  Engineering: Code2,
  'Quality & Security': ShieldCheck,
  Marketing: Megaphone,
  Documentation: BookMarked,
  Recovery: LifeBuoy,
  'System Ops': Cpu,
  Media: Sparkles,
}

export interface AgentCardProps {
  agent: AgentSummary
}

/**
 * AgentCard — one agent tile in the "AI Agents Status" grid: tinted IconTile,
 * agent name, short model label, and an online presence footer. Presentational;
 * the assembler supplies `agent`.
 */
export function AgentCard({ agent }: AgentCardProps) {
  const Icon = DEPARTMENT_ICON[agent.department] ?? Bot
  const reduce = useReducedMotion()
  const view = statusView(agent.status)

  return (
    <motion.div
      whileHover={reduce ? undefined : { scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 320, damping: 26 }}
    >
      <GlassCard interactive glow={agent.accent} padding="sm" className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <IconTile accent={agent.accent} size="sm" icon={Icon} />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium leading-snug text-zinc-100">{agent.name}</p>
            <p className="mt-0.5 break-words text-xs leading-snug text-zinc-500">{agent.modelLabel}</p>
          </div>
        </div>
        <div className="flex items-center justify-between border-t border-white/[0.06] pt-2.5">
          <StatusDot status={view.dot} pulse={view.pulse && !reduce} label={view.label} />
        </div>
      </GlassCard>
    </motion.div>
  )
}
