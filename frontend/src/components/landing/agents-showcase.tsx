/**
 * AgentsShowcase — the landing's "meet the company" section. An interactive explorer over the
 * REAL Omnivra org: 10 departments, 23 agents, each with the exact model it runs, its provider,
 * and the tools/duties it owns (mirrors backend/app/agents/registry.py — keep in sync). A
 * department rail (tabs) drives an animated roster panel; everything is keyboard-accessible and
 * reduced-motion aware.
 */
import { useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import {
  BellRing,
  BookMarked,
  Bot,
  Clapperboard,
  Code2,
  Compass,
  Cpu,
  Crown,
  Database,
  FileSearch,
  Globe,
  ImagePlus,
  LayoutTemplate,
  Megaphone,
  Mic,
  MonitorSmartphone,
  PenTool,
  Presentation,
  RotateCcw,
  Route,
  ScanSearch,
  Server,
  ShieldCheck,
  Split,
  Volume2,
  Webhook,
  type LucideIcon,
} from 'lucide-react'

import { GeminiMark, GroqMark, HuggingFaceMark, OpenRouterMark } from '@/components/landing/brand-marks'
import { cn } from '@/lib/utils'

const EASE = [0.22, 1, 0.36, 1] as const

type ProviderId = 'gemini' | 'openrouter' | 'groq' | 'huggingface'

const PROVIDER_META: Record<ProviderId, { label: string; Mark: React.ComponentType<{ className?: string }> }> = {
  gemini: { label: 'Gemini', Mark: GeminiMark },
  openrouter: { label: 'OpenRouter', Mark: OpenRouterMark },
  groq: { label: 'Groq', Mark: GroqMark },
  huggingface: { label: 'Hugging Face', Mark: HuggingFaceMark },
}

interface AgentCard {
  name: string
  icon: LucideIcon
  model: string
  provider: ProviderId
  tools: string[]
}

interface Dept {
  id: string
  name: string
  icon: LucideIcon
  accent: string
  tagline: string
  agents: AgentCard[]
}

/** The real roster (backend/app/agents/registry.py is the source of truth). */
const DEPARTMENTS: Dept[] = [
  {
    id: 'executive',
    name: 'Executive',
    icon: Crown,
    accent: 'cyan',
    tagline: 'Plans the work, staffs the run, and owns the outcome — your single point of contact.',
    agents: [
      { name: 'CEO / Manager', icon: Crown, model: 'gemini-3.1-flash-lite', provider: 'gemini', tools: ['Planning', 'Orchestration', 'Delegation', 'Approvals'] },
    ],
  },
  {
    id: 'architecture',
    name: 'Architecture',
    icon: Compass,
    accent: 'violet',
    tagline: 'Turns an idea into a system design and a file-by-file build manifest.',
    agents: [
      { name: 'Solution Architect', icon: Compass, model: 'gpt-oss-120b', provider: 'openrouter', tools: ['System design', 'File manifest'] },
    ],
  },
  {
    id: 'design',
    name: 'Design',
    icon: PenTool,
    accent: 'pink',
    tagline: 'Wireframes, design systems, and component specs before a line of UI is written.',
    agents: [
      { name: 'UI/UX Designer', icon: LayoutTemplate, model: 'gemini-3.1-flash-lite', provider: 'gemini', tools: ['Wireframes', 'Design system', 'Component specs'] },
    ],
  },
  {
    id: 'engineering',
    name: 'Engineering',
    icon: Code2,
    accent: 'blue',
    tagline: 'A four-person squad that ships the schema, the API, the backend, and the frontend.',
    agents: [
      { name: 'Database Engineer', icon: Database, model: 'nemotron-3-super-120b', provider: 'openrouter', tools: ['Schema design', 'Migrations', 'pgvector'] },
      { name: 'Backend Engineer', icon: Server, model: 'glm-4.5-air', provider: 'openrouter', tools: ['FastAPI services', 'Business logic'] },
      { name: 'Frontend Engineer', icon: MonitorSmartphone, model: 'laguna-xs.2', provider: 'openrouter', tools: ['React components', 'State', 'Styling'] },
      { name: 'API Engineer', icon: Webhook, model: 'glm-4.5-air', provider: 'openrouter', tools: ['Endpoint design', 'Contracts', 'Integration'] },
    ],
  },
  {
    id: 'quality',
    name: 'Quality & Security',
    icon: ShieldCheck,
    accent: 'emerald',
    tagline: 'Test plans, audits, and hardening on everything the other departments produce.',
    agents: [
      { name: 'QA Engineer', icon: ScanSearch, model: 'gemini-3.1-flash-lite', provider: 'gemini', tools: ['Test plans', 'Test code', 'Validation'] },
      { name: 'SecOps Engineer', icon: ShieldCheck, model: 'gpt-oss-120b', provider: 'openrouter', tools: ['Threat modeling', 'Audits', 'Hardening'] },
    ],
  },
  {
    id: 'marketing',
    name: 'Marketing',
    icon: Megaphone,
    accent: 'amber',
    tagline: 'Research, strategy, and short-form production for every launch.',
    agents: [
      { name: 'SEO Researcher', icon: Globe, model: 'groq/compound', provider: 'groq', tools: ['Keyword research', 'SERP analysis'] },
      { name: 'Social Strategist', icon: Megaphone, model: 'kimi-k2.6', provider: 'openrouter', tools: ['Content strategy', 'Campaigns'] },
      { name: 'Reel Automation', icon: Clapperboard, model: 'llama-3.1-8b-instant', provider: 'groq', tools: ['Short-form scripts', 'Reel automation'] },
    ],
  },
  {
    id: 'documentation',
    name: 'Documentation',
    icon: BookMarked,
    accent: 'violet',
    tagline: 'READMEs, guides, and boardroom-ready decks — rendered to real files.',
    agents: [
      { name: 'Documentation Agent', icon: BookMarked, model: 'gemma-4-31b', provider: 'openrouter', tools: ['Docs', 'READMEs', 'Guides'] },
      { name: 'Presentation Designer', icon: Presentation, model: 'gemma-4-31b', provider: 'openrouter', tools: ['Slide decks', 'PPTX export'] },
    ],
  },
  {
    id: 'recovery',
    name: 'Recovery',
    icon: RotateCcw,
    accent: 'cyan',
    tagline: 'Every run is checkpointed — this agent resumes any failure from the last good state.',
    agents: [
      { name: 'Recovery Agent', icon: RotateCcw, model: 'nemotron-3-super-120b', provider: 'openrouter', tools: ['Checkpoint recovery', 'Resume'] },
    ],
  },
  {
    id: 'system-ops',
    name: 'System Ops',
    icon: Cpu,
    accent: 'blue',
    tagline: 'The invisible crew that classifies, routes, recalls, notifies, and watches the logs.',
    agents: [
      { name: 'Task Classifier', icon: Split, model: 'lfm-2.5-thinking', provider: 'openrouter', tools: ['Task classification'] },
      { name: 'Workflow Router', icon: Route, model: 'lfm-2.5-thinking', provider: 'openrouter', tools: ['Department routing'] },
      { name: 'Memory Retrieval', icon: FileSearch, model: 'lfm-2.5-thinking', provider: 'openrouter', tools: ['Semantic recall', 'pgvector'] },
      { name: 'Notification Agent', icon: BellRing, model: 'lfm-2.5-thinking', provider: 'openrouter', tools: ['Alerts', 'Channels'] },
      { name: 'Log Analyzer', icon: Cpu, model: 'lfm-2.5-thinking', provider: 'openrouter', tools: ['Log analysis', 'Anomalies'] },
    ],
  },
  {
    id: 'media',
    name: 'Media',
    icon: Clapperboard,
    accent: 'pink',
    tagline: 'Voice in, voice out, images on demand — the studio behind reels and documents.',
    agents: [
      { name: 'Speech-to-Text', icon: Mic, model: 'whisper-large-v3-turbo', provider: 'groq', tools: ['Transcription'] },
      { name: 'Text-to-Speech', icon: Volume2, model: 'orpheus-v1-english', provider: 'groq', tools: ['Voice synthesis'] },
      { name: 'Image Generation', icon: ImagePlus, model: 'FLUX.1-schnell', provider: 'huggingface', tools: ['Image generation'] },
    ],
  },
]

const ACCENT_TEXT: Record<string, string> = {
  cyan: 'text-omnivra-cyan',
  blue: 'text-omnivra-blue',
  violet: 'text-omnivra-violet',
  emerald: 'text-omnivra-emerald-bright',
  amber: 'text-omnivra-amber',
  pink: 'text-omnivra-pink',
}
const ACCENT_ACTIVE: Record<string, string> = {
  cyan: 'border-omnivra-cyan/40 bg-omnivra-cyan/[0.08] text-omnivra-cyan',
  blue: 'border-omnivra-blue/40 bg-omnivra-blue/[0.08] text-omnivra-blue',
  violet: 'border-omnivra-violet/40 bg-omnivra-violet/[0.08] text-omnivra-violet',
  emerald: 'border-omnivra-emerald-bright/40 bg-omnivra-emerald-bright/[0.08] text-omnivra-emerald-bright',
  amber: 'border-omnivra-amber/40 bg-omnivra-amber/[0.08] text-omnivra-amber',
  pink: 'border-omnivra-pink/40 bg-omnivra-pink/[0.08] text-omnivra-pink',
}

export function AgentsShowcase() {
  const reduce = useReducedMotion() ?? false
  const [active, setActive] = useState(DEPARTMENTS[3].id) // Engineering — the biggest squad — first
  const dept = DEPARTMENTS.find((d) => d.id === active) ?? DEPARTMENTS[0]

  return (
    <div className="flex flex-col gap-6">
      {/* department rail — simple toggle buttons (not an ARIA tabs widget: Tab-key navigation,
          no roving focus), so aria-pressed is the honest semantic */}
      <div aria-label="Departments" className="flex flex-wrap gap-2">
        {DEPARTMENTS.map((d) => {
          const selected = d.id === active
          return (
            <button
              key={d.id}
              type="button"
              aria-pressed={selected}
              onClick={() => setActive(d.id)}
              className={cn(
                'focus-ring inline-flex items-center gap-2 rounded-full border px-3.5 py-2 text-xs font-semibold transition-all duration-200',
                selected
                  ? ACCENT_ACTIVE[d.accent]
                  : 'border-white/[0.08] bg-white/[0.02] text-[#a1a1aa] hover:border-white/20 hover:text-white',
              )}
            >
              <d.icon className="h-3.5 w-3.5" aria-hidden />
              {d.name}
              <span className={cn('rounded-full px-1.5 py-0.5 text-[10px] font-bold', selected ? 'bg-white/10' : 'bg-white/[0.05] text-[#a1a1aa]')}>
                {d.agents.length}
              </span>
            </button>
          )
        })}
      </div>

      {/* roster panel */}
      <AnimatePresence mode="wait">
        <motion.div
          key={dept.id}
          role="region"
          aria-label={`${dept.name} agents`}
          initial={reduce ? { opacity: 0 } : { opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduce ? { opacity: 0 } : { opacity: 0, y: -12 }}
          transition={{ duration: 0.35, ease: EASE }}
          className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]"
        >
          {/* department summary */}
          <div className="relative overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6">
            <div aria-hidden className="pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full bg-omnivra-cyan/[0.07] blur-3xl" />
            <span className={cn('grid h-12 w-12 place-items-center rounded-xl border border-white/[0.08] bg-white/[0.03]', ACCENT_TEXT[dept.accent])}>
              <dept.icon className="h-6 w-6" aria-hidden />
            </span>
            <h3 className="mt-4 text-xl font-bold text-white">{dept.name}</h3>
            <p className="mt-2 text-sm leading-relaxed text-[#a1a1aa]">{dept.tagline}</p>
            <p className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-white/[0.04] px-2.5 py-1 text-[11px] font-semibold text-[#d4d4d8]">
              <Bot className="h-3.5 w-3.5 text-omnivra-cyan" aria-hidden />
              {dept.agents.length} {dept.agents.length === 1 ? 'agent' : 'agents'}
            </p>
          </div>

          {/* agent cards */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {dept.agents.map((a, i) => {
              const P = PROVIDER_META[a.provider]
              return (
                <motion.div
                  key={a.name}
                  initial={reduce ? { opacity: 0 } : { opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, ease: EASE, delay: reduce ? 0 : 0.05 + i * 0.06 }}
                  className="group flex flex-col gap-3 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-4 transition-all duration-300 hover:-translate-y-0.5 hover:border-white/[0.15] hover:bg-white/[0.035]"
                >
                  <div className="flex items-center gap-3">
                    <span className={cn('grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-white/[0.08] bg-omnivra-surface-2/80 transition-transform duration-300 group-hover:scale-110', ACCENT_TEXT[dept.accent])}>
                      <a.icon className="h-5 w-5" aria-hidden />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-white">{a.name}</p>
                      <p className="flex items-center gap-1.5 text-[11px] text-[#a1a1aa]">
                        <P.Mark className="h-3.5 w-3.5 text-[9px]" />
                        {P.label}
                      </p>
                    </div>
                    <span className="relative flex h-1.5 w-1.5 shrink-0">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-omnivra-emerald opacity-60" />
                      <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-omnivra-emerald" />
                    </span>
                  </div>

                  <code className="w-fit max-w-full truncate rounded-md bg-omnivra-bg-root/60 px-2 py-1 font-mono text-[10px] text-omnivra-cyan/90">
                    {a.model}
                  </code>

                  <div className="flex flex-wrap gap-1.5">
                    {a.tools.map((t) => (
                      <span key={t} className="rounded-full border border-white/[0.07] bg-white/[0.03] px-2 py-0.5 text-[10px] font-medium text-[#d4d4d8]">
                        {t}
                      </span>
                    ))}
                  </div>
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
