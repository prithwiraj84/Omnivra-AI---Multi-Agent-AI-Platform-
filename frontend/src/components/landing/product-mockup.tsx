/**
 * ProductMockup — a polished, on-brand preview of the Omnivra command center, used as the landing
 * hero's centrepiece ("show the product", the way top AI-SaaS sites do). A glass app window with a
 * mini sidebar, greeting + Assign-to-CEO control, live stat cards with sparklines, an agent-status
 * strip, a task-execution area chart, and a live activity column. Subtle float + staggered reveal +
 * a glass sheen; all motion is auto-gated by the app-level <MotionConfig reducedMotion="user">.
 */
import { motion, type Variants } from 'framer-motion'
import { Bot, Boxes, LayoutDashboard, Sparkles, Wand2 } from 'lucide-react'

import { cn } from '@/lib/utils'

const EASE = [0.22, 1, 0.36, 1] as const
const stagger: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.06, delayChildren: 0.25 } } }
const item: Variants = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: EASE } } }

const STATS = [
  { label: 'Agents', value: '23', color: 'text-omnivra-cyan', spark: [4, 6, 5, 8, 7, 10, 9] },
  { label: 'Active tasks', value: '12', color: 'text-omnivra-blue', spark: [2, 3, 3, 5, 4, 6, 7] },
  { label: 'Runs', value: '48', color: 'text-omnivra-purple', spark: [9, 8, 12, 11, 14, 13, 16] },
  { label: 'Success', value: '100%', color: 'text-omnivra-emerald-bright', spark: [8, 9, 9, 10, 10, 10, 10] },
]
const AGENTS = [
  { name: 'Backend', dot: 'bg-omnivra-blue', working: true },
  { name: 'Frontend', dot: 'bg-omnivra-purple', working: true },
  { name: 'QA', dot: 'bg-omnivra-emerald-bright' },
  { name: 'SecOps', dot: 'bg-omnivra-cyan' },
  { name: 'Docs', dot: 'bg-omnivra-amber' },
]
const ACTIVITY = [
  { dot: 'bg-omnivra-blue', a: 'w-16', b: 'w-24' },
  { dot: 'bg-omnivra-purple', a: 'w-20', b: 'w-20' },
  { dot: 'bg-omnivra-emerald-bright', a: 'w-14', b: 'w-28' },
  { dot: 'bg-omnivra-cyan', a: 'w-24', b: 'w-16' },
]
const NAV = [LayoutDashboard, Boxes, Bot, Wand2]

function Spark({ data, className }: { data: number[]; className?: string }) {
  const max = Math.max(...data)
  const min = Math.min(...data)
  const pts = data
    .map((d, i) => `${(i / (data.length - 1)) * 100},${19 - ((d - min) / (max - min || 1)) * 16}`)
    .join(' ')
  return (
    <svg viewBox="0 0 100 20" preserveAspectRatio="none" className={cn('h-4 w-full', className)} aria-hidden>
      <polyline points={pts} fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function ProductMockup() {
  return (
    <div className="relative w-full">
      {/* glow behind the window */}
      <div aria-hidden className="pointer-events-none absolute -inset-x-16 -top-10 bottom-0 bg-glow-cyan blur-2xl" />
      <div aria-hidden className="pointer-events-none absolute inset-x-1/4 -bottom-8 h-40 rounded-full bg-omnivra-purple/25 blur-[80px]" />

      <motion.div
        initial={{ opacity: 0, y: 40, rotateX: 8 }}
        animate={{ opacity: 1, y: [0, -8, 0], rotateX: 0 }}
        transition={{
          opacity: { duration: 0.8, ease: EASE },
          rotateX: { duration: 0.8, ease: EASE },
          y: { duration: 7, repeat: Infinity, ease: 'easeInOut', delay: 0.8 },
        }}
        style={{ transformPerspective: 1400 }}
        className="relative overflow-hidden rounded-2xl border border-white/[0.09] bg-gradient-to-b from-omnivra-surface-2/90 to-omnivra-bg/95 shadow-panel ring-1 ring-white/[0.04] backdrop-blur-glass"
      >
        {/* glass sheen sweep */}
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 -left-1/2 w-1/2 -skew-x-12 bg-gradient-to-r from-transparent via-white/[0.06] to-transparent"
          animate={{ x: ['0%', '340%'] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut', repeatDelay: 3 }}
        />

        {/* title bar */}
        <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-omnivra-red/80" />
          <span className="h-2.5 w-2.5 rounded-full bg-omnivra-amber/80" />
          <span className="h-2.5 w-2.5 rounded-full bg-omnivra-emerald-bright/80" />
          <span className="mx-auto flex items-center gap-1.5 rounded-md bg-white/[0.04] px-3 py-1 text-[10px] font-medium text-[#a1a1aa]">
            <span className="h-1.5 w-1.5 rounded-full bg-omnivra-emerald-bright" />
            omnivra.app / command center
          </span>
        </div>

        <motion.div variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true }} className="flex">
          {/* sidebar */}
          <div className="hidden w-40 shrink-0 flex-col gap-2 border-r border-white/[0.05] p-3 sm:flex">
            <div className="mb-2 flex items-center gap-2">
              <span className="grid h-6 w-6 place-items-center rounded-md bg-gradient-to-br from-omnivra-cyan to-omnivra-purple">
                <Boxes className="h-3.5 w-3.5 text-omnivra-bg-root" strokeWidth={2.5} aria-hidden />
              </span>
              <span className="text-[11px] font-bold text-white">OMNIVRA</span>
            </div>
            {NAV.map((Icon, i) => (
              <motion.div
                key={i}
                variants={item}
                className={cn(
                  'flex items-center gap-2 rounded-md px-2 py-1.5',
                  i === 0 ? 'bg-omnivra-cyan/[0.12] text-omnivra-cyan' : 'text-[#71717a]',
                )}
              >
                <Icon className="h-3.5 w-3.5" aria-hidden />
                <span className={cn('h-1.5 rounded-full', i === 0 ? 'w-14 bg-omnivra-cyan/40' : 'w-16 bg-white/10')} />
              </motion.div>
            ))}
            <div className="mt-auto flex items-center gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] p-2">
              <span className="h-6 w-6 rounded-full bg-gradient-to-br from-omnivra-cyan to-omnivra-purple" />
              <div className="flex flex-col gap-1">
                <span className="h-1.5 w-12 rounded-full bg-white/15" />
                <span className="h-1.5 w-8 rounded-full bg-white/[0.08]" />
              </div>
            </div>
          </div>

          {/* main */}
          <div className="min-w-0 flex-1 p-4">
            <motion.div variants={item} className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-white">Good morning, Omnivra 👋</p>
                <p className="text-[11px] text-[#71717a]">Your AI company is running at full capacity.</p>
              </div>
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-omnivra-cyan to-omnivra-blue px-3 py-1.5 text-[11px] font-semibold text-omnivra-bg-root">
                <Sparkles className="h-3 w-3" aria-hidden /> Assign to CEO
              </span>
            </motion.div>

            {/* stat cards */}
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {STATS.map((s) => (
                <motion.div key={s.label} variants={item} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-2.5">
                  <p className="text-[10px] uppercase tracking-wide text-[#71717a]">{s.label}</p>
                  <p className="mt-0.5 text-lg font-bold text-white">{s.value}</p>
                  <div className={s.color}>
                    <Spark data={s.spark} />
                  </div>
                </motion.div>
              ))}
            </div>

            {/* agent status strip */}
            <motion.div variants={item} className="mt-4">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-[#71717a]">AI agents status</p>
              <div className="flex flex-wrap gap-1.5">
                {AGENTS.map((a) => (
                  <span key={a.name} className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.07] bg-white/[0.03] px-2 py-1 text-[10px] text-[#d4d4d8]">
                    <span className="relative flex h-1.5 w-1.5">
                      {a.working && <span className={cn('absolute inline-flex h-full w-full animate-ping rounded-full opacity-75', a.dot)} />}
                      <span className={cn('relative inline-flex h-1.5 w-1.5 rounded-full', a.dot)} />
                    </span>
                    {a.name}
                  </span>
                ))}
              </div>
            </motion.div>

            {/* mini area chart */}
            <motion.div variants={item} className="mt-4 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-[#71717a]">Task execution</p>
              <svg viewBox="0 0 200 56" preserveAspectRatio="none" className="h-14 w-full" aria-hidden>
                <defs>
                  <linearGradient id="mk-area" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path d="M0 44 L28 38 L56 40 L84 26 L112 30 L140 16 L168 20 L200 8 L200 56 L0 56 Z" fill="url(#mk-area)" />
                <path d="M0 44 L28 38 L56 40 L84 26 L112 30 L140 16 L168 20 L200 8" fill="none" stroke="#22d3ee" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </motion.div>
          </div>

          {/* activity column */}
          <div className="hidden w-44 shrink-0 flex-col gap-2 border-l border-white/[0.05] p-3 lg:flex">
            <p className="mb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-[#71717a]">
              <span className="h-1.5 w-1.5 rounded-full bg-omnivra-emerald-bright" /> Live activity
            </p>
            {ACTIVITY.map((r, i) => (
              <motion.div key={i} variants={item} className="flex items-center gap-2 rounded-lg border border-white/[0.05] bg-white/[0.02] p-2">
                <span className={cn('h-5 w-5 shrink-0 rounded-md', r.dot, 'opacity-80')} />
                <div className="flex flex-col gap-1">
                  <span className={cn('h-1.5 rounded-full bg-white/15', r.a)} />
                  <span className={cn('h-1.5 rounded-full bg-white/[0.08]', r.b)} />
                </div>
              </motion.div>
            ))}
            <div className="mt-1 rounded-lg border border-omnivra-amber/20 bg-omnivra-amber/[0.06] p-2 text-[10px] text-omnivra-amber">
              1 approval pending
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}
