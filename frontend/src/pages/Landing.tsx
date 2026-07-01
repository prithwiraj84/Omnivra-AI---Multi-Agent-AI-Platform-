/**
 * Landing — the public marketing front page (route "/"). A high-tech, 3D, scroll-animated showcase
 * of Omnivra AI Company OS on the product's dark/cyan-purple/glass theme. Lazy react-three-fiber hero
 * (WebGL-guarded), scroll parallax, 3D-tilt bento features, a scrollytelling pipeline, animated
 * department grid + stat counters, and a glowing CTA. Everything honors prefers-reduced-motion.
 */
import { Component, lazy, Suspense, useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  animate,
  motion,
  useInView,
  useMotionValue,
  useReducedMotion,
  useScroll,
  useSpring,
  useTransform,
  type Variants,
} from 'framer-motion'
import {
  ArrowRight,
  BadgeCheck,
  BookMarked,
  Bot,
  Boxes,
  Brain,
  Clapperboard,
  Code2,
  Compass,
  Cpu,
  Crown,
  Database,
  FilePlus2,
  Github,
  ImagePlus,
  Loader2,
  Megaphone,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Workflow,
  type LucideIcon,
} from 'lucide-react'

import { LandingNav } from '@/components/landing/landing-nav'
import { ProductMockup } from '@/components/landing/product-mockup'
import { useSupabaseAuth, type OAuthProvider } from '@/hooks/useSupabaseAuth'
import { cn } from '@/lib/utils'

const HeroCanvas = lazy(() => import('@/components/landing/hero-canvas'))
const EASE = [0.22, 1, 0.36, 1] as const

// --- motion helpers ---------------------------------------------------------
const rise: Variants = {
  hidden: { opacity: 0, y: 26 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: EASE } },
}
const container: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
}

/** WebGL guard: if the 3D scene throws (no WebGL / context loss), show the CSS glow instead. */
class SceneBoundary extends Component<{ fallback: ReactNode; children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children
  }
}

/** CSS fallback for the 3D core (also the Suspense fallback while the chunk loads). */
function HeroGlow() {
  return (
    <div aria-hidden className="absolute inset-0 grid place-items-center">
      <div className="h-72 w-72 animate-pulse-slow rounded-full bg-omnivra-cyan/25 blur-3xl" />
      <div className="absolute h-56 w-56 animate-float rounded-full bg-omnivra-purple/25 blur-3xl" />
    </div>
  )
}

/** A card that tilts in 3D toward the pointer. */
function TiltCard({ children, className }: { children: ReactNode; className?: string }) {
  const reduce = useReducedMotion()
  const rx = useMotionValue(0)
  const ry = useMotionValue(0)
  const srx = useSpring(rx, { stiffness: 150, damping: 17 })
  const sry = useSpring(ry, { stiffness: 150, damping: 17 })
  return (
    <motion.div
      onMouseMove={(e) => {
        if (reduce) return
        const r = (e.currentTarget as HTMLDivElement).getBoundingClientRect()
        ry.set(((e.clientX - r.left) / r.width - 0.5) * 9)
        rx.set(-((e.clientY - r.top) / r.height - 0.5) * 9)
      }}
      onMouseLeave={() => {
        rx.set(0)
        ry.set(0)
      }}
      style={{ rotateX: srx, rotateY: sry, transformPerspective: 900, transformStyle: 'preserve-3d' }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/** Count up to `to` when scrolled into view. */
function CountUp({ to, suffix = '' }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })
  const reduce = useReducedMotion()
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!inView) return
    if (reduce) return setVal(to)
    const controls = animate(0, to, { duration: 1.3, ease: EASE, onUpdate: (v) => setVal(Math.round(v)) })
    return () => controls.stop()
  }, [inView, to, reduce])
  return (
    <span ref={ref}>
      {val}
      {suffix}
    </span>
  )
}

function Section({ children, className, id }: { children: ReactNode; className?: string; id?: string }) {
  return (
    <motion.section
      id={id}
      variants={container}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: '-90px' }}
      className={cn('relative mx-auto w-full max-w-6xl px-5', className)}
    >
      {children}
    </motion.section>
  )
}

function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <motion.p
      variants={rise}
      className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-omnivra-cyan"
    >
      <Sparkles className="h-3 w-3" aria-hidden />
      {children}
    </motion.p>
  )
}

// --- content ----------------------------------------------------------------
const FEATURES: { icon: LucideIcon; title: string; body: string; accent: string; wide?: boolean }[] = [
  { icon: Workflow, title: 'Multi-agent orchestration', body: 'A CEO agent plans your task, delegates across departments, and threads each specialist’s output into the next — a whole company working in one run.', accent: 'cyan', wide: true },
  { icon: FilePlus2, title: 'Document Studio', body: '20 writing genres × your color + font, rendered to real PPTX / DOCX / PDF with charts and FLUX images.', accent: 'blue' },
  { icon: Clapperboard, title: 'Social Studio', body: 'Reels and posts — storyboarded, voiced, and rendered, gated behind your approval before publish.', accent: 'purple' },
  { icon: Boxes, title: 'Universal app runner', body: 'One click builds a per-app venv / npm install and serves the generated backend + frontend — then “Open app.”', accent: 'emerald', wide: true },
  { icon: Brain, title: 'Knowledge & memory', body: 'Per-project RAG over your docs + agent memory (pgvector) so runs build on what came before.', accent: 'violet' },
  { icon: BadgeCheck, title: 'Human approval gate', body: 'Nothing ships without you. Every deliverable pauses at the gate for a one-click approve or reject.', accent: 'amber' },
]

const DEPARTMENTS: { icon: LucideIcon; name: string; accent: string }[] = [
  { icon: Crown, name: 'Executive', accent: 'cyan' },
  { icon: Compass, name: 'Architecture', accent: 'violet' },
  { icon: ImagePlus, name: 'Design', accent: 'pink' },
  { icon: Code2, name: 'Engineering', accent: 'blue' },
  { icon: ShieldCheck, name: 'Quality & Security', accent: 'emerald' },
  { icon: Megaphone, name: 'Marketing', accent: 'amber' },
  { icon: BookMarked, name: 'Documentation', accent: 'violet' },
  { icon: RotateCcw, name: 'Recovery', accent: 'cyan' },
  { icon: Cpu, name: 'System Ops', accent: 'blue' },
  { icon: ImagePlus, name: 'Media', accent: 'pink' },
]

const STATS = [
  { to: 23, suffix: '', label: 'AI agents' },
  { to: 10, suffix: '', label: 'Departments' },
  { to: 20, suffix: '', label: 'Document genres' },
  { to: 4, suffix: '', label: 'LLM providers' },
]

const STEPS: { n: string; title: string; body: string; icon: LucideIcon }[] = [
  { n: '01', title: 'Assign a task to your CEO', body: 'Describe an outcome in plain language — “build a todo app”, “write an investor brief”, “ship a launch reel.”', icon: Bot },
  { n: '02', title: 'Agents plan & delegate', body: 'The CEO drafts a plan and routes work to the right departments; specialists run in sequence, sharing context.', icon: Workflow },
  { n: '03', title: 'They build, write & render', body: 'Code files, documents, media and full apps land in your workspace — real artifacts, not mock-ups.', icon: Code2 },
  { n: '04', title: 'You review, approve & ship', body: 'Everything waits at the approval gate. Approve to publish, or run the generated app right from the workspace.', icon: BadgeCheck },
]

const PROVIDERS = ['OpenRouter', 'Groq', 'Google Gemini', 'Hugging Face', 'Supabase', 'LangGraph', 'FastAPI', 'React']
const ACCENT_TEXT: Record<string, string> = {
  cyan: 'text-omnivra-cyan', blue: 'text-omnivra-blue', purple: 'text-omnivra-purple',
  violet: 'text-omnivra-violet', emerald: 'text-omnivra-emerald-bright', amber: 'text-omnivra-amber', pink: 'text-omnivra-pink',
}
const ACCENT_GLOW: Record<string, string> = {
  cyan: 'group-hover:shadow-neon-cyan', blue: 'group-hover:shadow-neon-blue', purple: 'group-hover:shadow-neon-violet',
  violet: 'group-hover:shadow-neon-violet', emerald: 'group-hover:shadow-neon-emerald', amber: 'group-hover:shadow-neon-cyan', pink: 'group-hover:shadow-neon-violet',
}

function GoogleMark() {
  return (
    <svg viewBox="0 0 24 24" className="h-[18px] w-[18px]" aria-hidden>
      <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.24 1.5-1.7 4.4-5.5 4.4-3.3 0-6-2.7-6-6.1s2.7-6.1 6-6.1c1.9 0 3.2.8 3.9 1.5l2.7-2.6C16.9 3 14.7 2 12 2 6.9 2 2.8 6.1 2.8 12S6.9 22 12 22c6.1 0 8.4-4.3 8.4-6.5 0-.4 0-.7-.1-1.1H12z" />
    </svg>
  )
}

// --- page -------------------------------------------------------------------
export function Landing() {
  const reduce = useReducedMotion() ?? false
  const navigate = useNavigate()
  const { isConfigured, signInWithProvider } = useSupabaseAuth()
  const [oauthPending, setOauthPending] = useState<OAuthProvider | null>(null)
  const [oauthError, setOauthError] = useState<string | null>(null)

  // CTA "Continue with …": start OAuth directly when Supabase is set up, else route to the
  // sign-in page (which also carries the credentials fallback). Shows a pending state during
  // the async round-trip and surfaces failures in place instead of silently bouncing away.
  async function startOAuth(provider: OAuthProvider) {
    if (!isConfigured) {
      navigate('/login')
      return
    }
    setOauthError(null)
    setOauthPending(provider)
    try {
      await signInWithProvider(provider) // browser redirects away on success
    } catch {
      setOauthError('Could not start sign-in. Make sure this provider is enabled in your Supabase project.')
      setOauthPending(null)
    }
  }

  // Only mount the 3D scene when WebGL is actually available (skips it in jsdom/tests + on GPUs that
  // can't; the CSS HeroGlow shows instead). Starts false so the very first paint is the fallback.
  const [webgl, setWebgl] = useState(false)
  useEffect(() => {
    try {
      const c = document.createElement('canvas')
      setWebgl(!!(c.getContext('webgl') || c.getContext('experimental-webgl')))
    } catch {
      setWebgl(false)
    }
  }, [])

  const heroRef = useRef<HTMLDivElement>(null)
  const heroInView = useInView(heroRef) // pause the 3D render loop once the hero scrolls away
  const { scrollYProgress: heroP } = useScroll({ target: heroRef, offset: ['start start', 'end start'] })
  const heroY = useTransform(heroP, [0, 1], [0, 140])
  const heroScale = useTransform(heroP, [0, 1], [1, 0.9])
  const heroOpacity = useTransform(heroP, [0, 1], [1, 0])
  const sceneY = useTransform(heroP, [0, 1], [0, -80])

  const stepsRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress: stepsP } = useScroll({ target: stepsRef, offset: ['start 65%', 'end 55%'] })
  const lineScale = useSpring(stepsP, { stiffness: 90, damping: 24 })

  const { scrollYProgress: pageP } = useScroll()
  const barScale = useSpring(pageP, { stiffness: 120, damping: 30 })

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-omnivra-bg font-sans text-white">
      {/* top scroll-progress bar */}
      <motion.div style={{ scaleX: barScale }} className="fixed inset-x-0 top-0 z-[60] h-0.5 origin-left bg-gradient-to-r from-omnivra-cyan via-omnivra-blue to-omnivra-purple" />

      {/* ambient background layers — clipped to the viewport so the blur blobs never add h-scroll */}
      <div aria-hidden className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-grid-faint [background-size:44px_44px] opacity-[0.5]" />
        <div className="absolute inset-0 bg-ambient" />
        <motion.div
          className="absolute left-[-10%] top-[-8%] h-[46vh] w-[46vh] rounded-full bg-omnivra-cyan/[0.10] blur-[120px]"
          animate={reduce ? undefined : { x: [0, 40, 0], y: [0, 30, 0] }}
          transition={{ duration: 16, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute right-[-8%] top-[10%] h-[40vh] w-[40vh] rounded-full bg-omnivra-purple/[0.10] blur-[120px]"
          animate={reduce ? undefined : { x: [0, -30, 0], y: [0, 40, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      <LandingNav />

      {/* ============================= HERO ============================= */}
      <section ref={heroRef} className="relative overflow-hidden pb-16 pt-28 sm:pb-24 sm:pt-36">
        {/* aurora + subtle particle sphere as ambient depth behind the product */}
        <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 h-[80vh] bg-glow-cyan" />
        <motion.div aria-hidden style={reduce ? undefined : { y: sceneY }} className="absolute inset-0 z-0 opacity-60">
          {webgl ? (
            <SceneBoundary fallback={<HeroGlow />}>
              <Suspense fallback={<HeroGlow />}>
                <HeroCanvas reduced={reduce} active={heroInView} />
              </Suspense>
            </SceneBoundary>
          ) : (
            <HeroGlow />
          )}
        </motion.div>

        <div className="relative z-10 mx-auto max-w-6xl px-5">
        <motion.div
          style={reduce ? undefined : { scale: heroScale, opacity: heroOpacity }}
          className="mx-auto flex max-w-3xl flex-col items-center text-center"
        >
          <motion.span
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6, ease: EASE }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.04] px-3.5 py-1.5 text-xs font-medium text-[#d4d4d8] backdrop-blur-glass"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-omnivra-emerald opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-omnivra-emerald" />
            </span>
            The AI Company Operating System
          </motion.span>

          <h1 className="text-balance text-5xl font-bold leading-[1.02] tracking-tight sm:text-6xl md:text-7xl">
            <motion.span
              initial={{ opacity: 0, y: 22 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.28, duration: 0.7, ease: EASE }}
              className="block"
            >
              Run an entire company
            </motion.span>
            <motion.span
              initial={{ opacity: 0, y: 22 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.7, ease: EASE }}
              className="block bg-gradient-to-r from-omnivra-cyan via-omnivra-blue to-omnivra-purple bg-clip-text text-transparent"
            >
              with a team of AI agents.
            </motion.span>
          </h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.55, duration: 0.6, ease: EASE }}
            className="mt-6 max-w-2xl text-pretty text-base text-[#a1a1aa] sm:text-lg"
          >
            Omnivra is a command center where a CEO agent delegates to <span className="text-white">23 specialists</span> across{' '}
            <span className="text-white">10 departments</span>. They design, code, write documents, produce media and ship apps
            — you just approve.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.6, ease: EASE }}
            className="mt-9 flex flex-col items-center gap-3 sm:flex-row"
          >
            <Link
              to="/dashboard"
              className="focus-ring group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-omnivra-cyan to-omnivra-blue px-6 py-3 text-sm font-semibold text-omnivra-bg-root shadow-neon-cyan transition-transform duration-200 hover:scale-[1.03] active:scale-95"
            >
              Launch the command center
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" aria-hidden />
            </Link>
            <a
              href="#how"
              className="focus-ring group inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-6 py-3 text-sm font-semibold text-white backdrop-blur-glass transition-colors hover:border-white/25"
            >
              <Play className="h-4 w-4 text-omnivra-cyan" aria-hidden />
              See how it works
            </a>
          </motion.div>
        </motion.div>

        {/* the product — the hero centrepiece */}
        <motion.div style={reduce ? undefined : { y: heroY }} className="mx-auto mt-14 max-w-4xl sm:mt-16">
          <ProductMockup />
        </motion.div>
        </div>

        {/* fade the hero into the page */}
        <div aria-hidden className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-b from-transparent to-omnivra-bg" />
      </section>

      {/* ===================== PROVIDER MARQUEE ===================== */}
      <div className="relative z-10 border-y border-white/[0.05] bg-omnivra-bg/60 py-5 backdrop-blur-glass">
        <p className="mb-3 text-center text-[11px] font-semibold uppercase tracking-[0.2em] text-[#71717a]">Built on</p>
        {/* the scrolling row is decorative + duplicated, so hide it from AT and expose the list once */}
        <div aria-hidden className="group relative flex overflow-hidden [mask-image:linear-gradient(90deg,transparent,#000_12%,#000_88%,transparent)]">
          <motion.div
            className="flex shrink-0 items-center gap-10 pr-10"
            animate={reduce ? undefined : { x: ['0%', '-50%'] }}
            transition={{ duration: 22, repeat: Infinity, ease: 'linear' }}
          >
            {[...PROVIDERS, ...PROVIDERS].map((p, i) => (
              <span key={i} className="whitespace-nowrap text-lg font-semibold text-[#71717a] transition-colors hover:text-white">
                {p}
              </span>
            ))}
          </motion.div>
        </div>
        <ul className="sr-only">
          {PROVIDERS.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      </div>

      {/* ========================= FEATURES ========================= */}
      <Section id="features" className="py-24 sm:py-32">
        <Eyebrow>Everything in one command center</Eyebrow>
        <motion.h2 variants={rise} className="max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">
          A studio for every kind of work your company does.
        </motion.h2>
        <motion.p variants={rise} className="mt-3 max-w-xl text-[#a1a1aa]">
          Orchestration, documents, media, apps, knowledge and approvals — one dark, fast, glassy workspace.
        </motion.p>

        <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <motion.div key={f.title} variants={rise} className={cn(f.wide && 'lg:col-span-2')}>
              <TiltCard className="h-full">
                <div
                  className={cn(
                    'group h-full rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 transition-all duration-300 hover:border-white/15',
                    ACCENT_GLOW[f.accent],
                  )}
                >
                  <div className={cn('mb-4 grid h-11 w-11 place-items-center rounded-xl border border-white/[0.08] bg-white/[0.03]', ACCENT_TEXT[f.accent])}>
                    <f.icon className="h-5 w-5" aria-hidden />
                  </div>
                  <h3 className="text-lg font-semibold text-white">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[#a1a1aa]">{f.body}</p>
                </div>
              </TiltCard>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* ========================= HOW IT WORKS ========================= */}
      <Section id="how" className="py-24 sm:py-28">
        <Eyebrow>How it works</Eyebrow>
        <motion.h2 variants={rise} className="max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">
          From one sentence to a shipped deliverable.
        </motion.h2>

        <div ref={stepsRef} className="relative mt-14 pl-8 sm:pl-10">
          {/* animated progress rail */}
          <div className="absolute left-[14px] top-2 h-[calc(100%-1rem)] w-px bg-white/[0.08] sm:left-[18px]" aria-hidden />
          <motion.div
            style={{ scaleY: lineScale }}
            className="absolute left-[14px] top-2 h-[calc(100%-1rem)] w-px origin-top bg-gradient-to-b from-omnivra-cyan to-omnivra-purple sm:left-[18px]"
            aria-hidden
          />
          <div className="flex flex-col gap-10">
            {STEPS.map((s) => (
              <motion.div key={s.n} variants={rise} className="relative">
                <span className="absolute -left-8 top-0 grid h-7 w-7 place-items-center rounded-full border border-white/10 bg-omnivra-surface-2 text-omnivra-cyan sm:-left-10">
                  <s.icon className="h-3.5 w-3.5" aria-hidden />
                </span>
                <div className="flex flex-col gap-1">
                  <span className="font-mono text-xs text-omnivra-cyan">{s.n}</span>
                  <h3 className="text-lg font-semibold text-white">{s.title}</h3>
                  <p className="max-w-xl text-sm leading-relaxed text-[#a1a1aa]">{s.body}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* ========================= DEPARTMENTS ========================= */}
      <Section id="departments" className="py-24 sm:py-28">
        <Eyebrow>10 departments, one payroll of zero</Eyebrow>
        <motion.h2 variants={rise} className="max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">
          Your org chart, staffed by specialists.
        </motion.h2>
        <div className="mt-12 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {DEPARTMENTS.map((d) => (
            <motion.div key={d.name} variants={rise}>
              <div className="group flex flex-col items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 text-center transition-all duration-300 hover:-translate-y-1 hover:border-white/15 hover:bg-white/[0.04]">
                <span className={cn('grid h-11 w-11 place-items-center rounded-xl border border-white/[0.08] bg-white/[0.03] transition-transform duration-300 group-hover:scale-110', ACCENT_TEXT[d.accent])}>
                  <d.icon className="h-5 w-5" aria-hidden />
                </span>
                <span className="text-sm font-medium text-[#d4d4d8]">{d.name}</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* stats */}
        <div className="mt-14 grid grid-cols-2 gap-4 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-8 sm:grid-cols-4">
          {STATS.map((s) => (
            <motion.div key={s.label} variants={rise} className="flex flex-col items-center text-center">
              <span className="bg-gradient-to-r from-omnivra-cyan to-omnivra-purple bg-clip-text text-4xl font-bold text-transparent sm:text-5xl">
                <CountUp to={s.to} suffix={s.suffix} />
              </span>
              <span className="mt-1 text-xs font-medium uppercase tracking-wider text-[#71717a]">{s.label}</span>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* ========================= CTA ========================= */}
      <Section className="py-24 sm:py-32">
        <motion.div variants={rise} className="relative overflow-hidden rounded-3xl border border-white/[0.08] bg-gradient-to-br from-omnivra-surface-2 to-omnivra-bg p-10 text-center sm:p-16">
          <div aria-hidden className="pointer-events-none absolute inset-0 bg-glow-cyan" />
          <div aria-hidden className="pointer-events-none absolute -bottom-24 left-1/2 h-64 w-[36rem] -translate-x-1/2 rounded-full bg-omnivra-purple/20 blur-[100px]" />
          <div className="relative z-10 mx-auto flex max-w-2xl flex-col items-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-5xl">
              Start your <span className="bg-gradient-to-r from-omnivra-cyan to-omnivra-purple bg-clip-text text-transparent">AI company</span> today.
            </h2>
            <p className="mt-4 text-[#a1a1aa]">Sign in and hand your first task to the CEO. It’s free to run on your own keys.</p>
            <div className="mt-8 flex w-full flex-col items-center gap-3 sm:flex-row sm:justify-center">
              <button
                type="button"
                onClick={() => startOAuth('google')}
                disabled={oauthPending !== null}
                className="focus-ring inline-flex w-full items-center justify-center gap-2.5 rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-semibold text-white backdrop-blur-glass transition-colors hover:border-white/25 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
              >
                {oauthPending === 'google' ? <Loader2 className="h-[18px] w-[18px] animate-spin" aria-hidden /> : <GoogleMark />}
                Continue with Google
              </button>
              <button
                type="button"
                onClick={() => startOAuth('github')}
                disabled={oauthPending !== null}
                className="focus-ring inline-flex w-full items-center justify-center gap-2.5 rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-semibold text-white backdrop-blur-glass transition-colors hover:border-white/25 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
              >
                {oauthPending === 'github' ? (
                  <Loader2 className="h-[18px] w-[18px] animate-spin" aria-hidden />
                ) : (
                  <Github className="h-[18px] w-[18px]" aria-hidden />
                )}
                Continue with GitHub
              </button>
            </div>
            {oauthError && (
              <p role="alert" aria-live="polite" className="mt-3 text-xs text-omnivra-pink">
                {oauthError}
              </p>
            )}
            <Link
              to="/dashboard"
              className="focus-ring group mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-omnivra-cyan hover:text-white"
            >
              or launch the command center
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" aria-hidden />
            </Link>
          </div>
        </motion.div>
      </Section>

      {/* ========================= FOOTER ========================= */}
      <footer className="relative z-10 border-t border-white/[0.06] py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-5 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-omnivra-cyan to-omnivra-purple">
              <Boxes className="h-4 w-4 text-omnivra-bg-root" strokeWidth={2.4} aria-hidden />
            </span>
            <span className="text-sm font-bold text-white">OMNIVRA</span>
            <span className="text-xs text-[#71717a]">AI Company OS</span>
          </div>
          <p className="flex items-center gap-1.5 text-xs text-[#71717a]">
            <Database className="h-3.5 w-3.5" aria-hidden /> React · FastAPI · LangGraph · Supabase
          </p>
          <p className="text-xs text-[#71717a]">© {new Date().getFullYear()} Omnivra</p>
        </div>
      </footer>
    </div>
  )
}
