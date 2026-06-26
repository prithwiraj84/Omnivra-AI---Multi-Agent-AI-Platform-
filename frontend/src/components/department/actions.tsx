/**
 * Department quick-action launcher + tailored panel (cp-0048).
 *  - DeptQuickAction: assign a task scoped to this department (CEO delegates within it).
 *  - DeptTailoredPanel: per-department contextual tips + quick links into the real tools.
 */
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import {
  BadgeCheck,
  BookOpen,
  Brain,
  CheckCircle2,
  Clapperboard,
  FilePlus2,
  FileText,
  Layers,
  LayoutGrid,
  ListChecks,
  Loader2,
  ScrollText,
  Send,
  Workflow,
  type LucideIcon,
} from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { Button } from '@/components/ui/button'
import { useRunWorkflow } from '@/hooks/useRunWorkflow'

/** Assign a task scoped to a department — the CEO then delegates within it. */
export function DeptQuickAction({ slug, title }: { slug: string; title: string }) {
  const [prompt, setPrompt] = useState('')
  const run = useRunWorkflow()
  const qc = useQueryClient()
  const busy = run.isPending

  const submit = (e: FormEvent) => {
    e.preventDefault()
    const p = prompt.trim()
    if (!p || busy) return
    run.mutate(
      { task: `For the ${title} department: ${p}` },
      {
        onSuccess: () => {
          setPrompt('')
          qc.invalidateQueries({ queryKey: ['department', slug] })
          qc.invalidateQueries({ queryKey: ['dashboard'] })
        },
      },
    )
  }

  return (
    <GlassCard padding="md" className="flex flex-col gap-3">
      <SectionHeader label={`Assign to ${title}`} />
      <form onSubmit={submit} className="flex flex-col gap-2.5">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={`Describe a task for the ${title} team…`}
          aria-label={`Task for ${title}`}
          rows={2}
          className="focus-ring min-h-[3.25rem] w-full resize-y rounded-md bg-omnivra-surface-2 px-3 py-2 text-sm text-[#e4e4e7] placeholder:text-[#71717a]"
        />
        <div className="flex items-center justify-between gap-2">
          {run.isSuccess && !prompt ? (
            <span className="inline-flex items-center gap-1.5 text-xs text-omnivra-emerald" role="status">
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden /> Assigned — agents are working
            </span>
          ) : (
            <span className="text-[11px] text-[#71717a]">Routed to the CEO, who delegates within {title}.</span>
          )}
          <Button type="submit" size="sm" disabled={busy || prompt.trim().length === 0}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Send className="h-4 w-4" aria-hidden />}
            {busy ? 'Assigning…' : 'Assign'}
          </Button>
        </div>
        {run.isError && (
          <p className="text-xs text-omnivra-pink" role="status">Could not assign the task. Is the backend running?</p>
        )}
      </form>
    </GlassCard>
  )
}

interface QuickLink {
  label: string
  to: string
  icon: LucideIcon
}

const TAILORED: Record<string, { tip: string; links: QuickLink[] }> = {
  executive: {
    tip: 'Set direction and delegate. The CEO plans the roadmap and routes work across every department.',
    links: [
      { label: 'Workflows', to: '/workflows', icon: Workflow },
      { label: 'Approvals', to: '/approvals', icon: BadgeCheck },
      { label: 'Tasks', to: '/tasks', icon: ListChecks },
    ],
  },
  architecture: {
    tip: 'Shape the system. Draft designs and file manifests, then hand them to engineering.',
    links: [
      { label: 'Document Studio', to: '/document-studio', icon: FilePlus2 },
      { label: 'Workspace', to: '/workspace', icon: LayoutGrid },
      { label: 'Documents', to: '/documents', icon: FileText },
    ],
  },
  engineering: {
    tip: 'Build the product. Generate real code files, browse the codebase, and run programs in the workspace.',
    links: [
      { label: 'Workspace (code)', to: '/workspace', icon: LayoutGrid },
      { label: 'Workflows', to: '/workflows', icon: Workflow },
      { label: 'Tasks', to: '/tasks', icon: ListChecks },
    ],
  },
  quality: {
    tip: 'Verify and harden. QA writes tests and SecOps reviews each build for vulnerabilities.',
    links: [
      { label: 'Workflows', to: '/workflows', icon: Workflow },
      { label: 'Reports', to: '/documents', icon: FileText },
      { label: 'Workspace', to: '/workspace', icon: LayoutGrid },
    ],
  },
  marketing: {
    tip: 'Reach the audience. Generate reels and posts, research SEO, and publish to social.',
    links: [
      { label: 'Social Studio', to: '/social', icon: Clapperboard },
      { label: 'Documents', to: '/documents', icon: FileText },
      { label: 'Knowledge', to: '/knowledge', icon: BookOpen },
    ],
  },
  documentation: {
    tip: 'Keep the company explainable. Generate docs and decks; index them for retrieval.',
    links: [
      { label: 'Document Studio', to: '/document-studio', icon: FilePlus2 },
      { label: 'Documents', to: '/documents', icon: FileText },
      { label: 'Knowledge Base', to: '/knowledge', icon: BookOpen },
    ],
  },
  'system-ops': {
    tip: 'Run the control plane. Classification, routing, memory, notifications and log analysis keep the OS healthy.',
    links: [
      { label: 'Logs', to: '/logs', icon: ScrollText },
      { label: 'Memory', to: '/memory', icon: Brain },
      { label: 'Knowledge', to: '/knowledge', icon: BookOpen },
    ],
  },
}

export function DeptTailoredPanel({ slug }: { slug: string }) {
  const cfg = TAILORED[slug]
  if (!cfg) return null
  return (
    <GlassCard padding="md" className="flex flex-col gap-3">
      <SectionHeader label="Department Tools" action={<Layers className="h-4 w-4 text-[#71717a]" aria-hidden />} />
      <p className="text-sm leading-relaxed text-[#a1a1aa]">{cfg.tip}</p>
      <div className="flex flex-wrap gap-2">
        {cfg.links.map((l) => {
          const Icon = l.icon
          return (
            <Link
              key={l.to}
              to={l.to}
              className="focus-ring inline-flex items-center gap-1.5 rounded-md border border-white/10 px-2.5 py-1.5 text-xs font-medium text-[#d4d4d8] transition-colors hover:border-omnivra-cyan/40 hover:text-omnivra-cyan"
            >
              <Icon className="h-3.5 w-3.5" aria-hidden />
              {l.label}
            </Link>
          )
        })}
      </div>
    </GlassCard>
  )
}
