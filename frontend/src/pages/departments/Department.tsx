import { useParams } from 'react-router-dom'
import { Users } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { EmptyState } from '@/components/ui/empty-state'
import { NeonBadge } from '@/components/ui/neon-badge'
import { AgentCard } from '@/components/dashboard/agent-card'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { AGENTS } from '@/config/agents'
import { navGroups } from '@/config/navigation'
import type { Accent, AgentSummary } from '@/types'

/**
 * Per-department display config. `title` is the human label shown in the header;
 * `departments` is the set of agent-roster `department` values that belong to this
 * page (the roster uses "System Ops" while the nav/title says "System Operations",
 * and Architecture surfaces both the "Architecture" and "Design" roster agents).
 * `note` is a short descriptor rendered beneath the header.
 */
interface DepartmentConfig {
  title: string
  departments: string[]
  note: string
}

const DEPARTMENTS: Record<string, DepartmentConfig> = {
  executive: {
    title: 'Executive',
    departments: ['Executive'],
    note: 'Strategic direction and delegation. The CEO / Manager plans the company roadmap and routes work to the right department.',
  },
  architecture: {
    title: 'Architecture',
    departments: ['Architecture', 'Design'],
    note: 'System design and user experience. Solution architects and designers shape how each build comes together.',
  },
  engineering: {
    title: 'Engineering',
    departments: ['Engineering'],
    note: 'The builders. Database, frontend, backend and API engineers turn plans into working software.',
  },
  quality: {
    title: 'Quality & Security',
    departments: ['Quality & Security'],
    note: 'Verification and hardening. QA and SecOps engineers test every build and scan it for vulnerabilities.',
  },
  marketing: {
    title: 'Marketing',
    departments: ['Marketing'],
    note: 'Reach and growth. SEO, social and reel-automation agents take the product to its audience.',
  },
  documentation: {
    title: 'Documentation',
    departments: ['Documentation'],
    note: 'Knowledge capture. Documentation and presentation agents keep the company explainable.',
  },
  'system-ops': {
    title: 'System Operations',
    departments: ['System Ops'],
    note: 'The control plane. Classification, routing, memory, notification and log-analysis utilities keep the OS running.',
  },
}

/** Look up the Departments nav accent for a given display title. */
function accentForTitle(title: string): Accent {
  const group = navGroups.find((g) => g.label === 'Departments')
  const item = group?.items.find((i) => i.label === title)
  return (item?.accent ?? 'cyan') as Accent
}

export interface DepartmentProps {
  /** Optional explicit title; otherwise resolved from the route `slug` param. */
  title?: string
  /** Optional explicit slug; otherwise read from the route `slug` param. */
  slug?: string
}

/**
 * Department — the per-department roster page. Resolves the route `slug` (e.g.
 * "engineering") to a display title + the matching roster departments, then renders
 * a header (SectionHeader with the dept accent + agent count) and a staggered grid
 * of the department's AgentCards. Falls back to an EmptyState when the slug is
 * unknown or no agents match.
 */
export function Department({ title: titleProp, slug: slugProp }: DepartmentProps = {}) {
  const params = useParams<{ slug: string }>()
  const slug = slugProp ?? params.slug ?? ''
  const config = DEPARTMENTS[slug]

  const title = titleProp ?? config?.title ?? 'Department'
  const accent = accentForTitle(title)
  const note = config?.note

  const agents: AgentSummary[] = config
    ? AGENTS.filter((a) => config.departments.includes(a.department))
    : []

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <GlassCard padding="md" glow={accent} className="flex flex-col gap-3">
          <SectionHeader
            label={title}
            count={agents.length}
            action={<NeonBadge tone="cyan">Department</NeonBadge>}
          />
          {note && <p className="max-w-prose text-sm leading-relaxed text-[#a1a1aa]">{note}</p>}
        </GlassCard>
      </Reveal>

      {agents.length === 0 ? (
        <GlassCard padding="none" className="overflow-hidden">
          <EmptyState
            icon={Users}
            title="No agents in this department"
            hint="This department has no registered agents yet. Check the roster or pick another department."
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
    </div>
  )
}
