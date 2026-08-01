import { Cpu } from 'lucide-react'
import { Chip } from '@/components/ui/chip'
import type { AgentSummary } from '@/types'

export interface SystemOpsRowProps {
  ops: AgentSummary[]
}

/**
 * SystemOpsRow — the compact "SYSTEM OPERATIONS" sub-panel beneath the agent
 * grid: a section label + "(North Mini Code)" caption and a wrap of online ops chips.
 * Presentational; the assembler supplies `ops`.
 */
export function SystemOpsRow({ ops }: SystemOpsRowProps) {
  return (
    <div className="mt-4 rounded-lg border border-white/[0.06] bg-omnivra-surface p-3">
      <div className="mb-2.5 flex items-center gap-2">
        <span className="section-label">System Operations</span>
        <span className="text-[10px] font-medium text-zinc-600">(North Mini Code)</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {ops.map((op) => (
          <Chip key={op.id} label={op.name} icon={Cpu} accent="cyan" status="online" />
        ))}
      </div>
    </div>
  )
}
