/** LandingNav — a glass, scroll-aware top bar for the marketing landing. Transparent at the top,
 *  it gains a blurred border + background once you scroll. Links smooth-scroll to sections; the CTA
 *  launches the app. */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useMotionValueEvent, useScroll } from 'framer-motion'
import { ArrowRight, Boxes } from 'lucide-react'

import { useSupabaseAuth } from '@/hooks/useSupabaseAuth'
import { cn } from '@/lib/utils'

const LINKS = [
  { label: 'Features', href: '#features' },
  { label: 'Agents', href: '#agents' },
  { label: 'How it works', href: '#how' },
  { label: 'Integrations', href: '#stack' },
]

export function LandingNav() {
  const { scrollY } = useScroll()
  const [scrolled, setScrolled] = useState(false)
  useMotionValueEvent(scrollY, 'change', (y) => setScrolled(y > 24))
  const { isAuthenticated } = useSupabaseAuth()

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        'fixed inset-x-0 top-0 z-50 transition-colors duration-300',
        scrolled ? 'border-b border-white/[0.06] bg-omnivra-bg/70 backdrop-blur-glass' : 'border-b border-transparent',
      )}
    >
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
        <Link to="/" className="focus-ring group flex items-center gap-2.5 rounded-md">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-omnivra-cyan to-omnivra-purple shadow-neon-cyan">
            <Boxes className="h-[18px] w-[18px] text-omnivra-bg-root" strokeWidth={2.4} aria-hidden />
          </span>
          <span className="text-sm font-bold tracking-tight text-white">
            OMNIVRA<span className="text-omnivra-cyan">.</span>
          </span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="focus-ring rounded-md px-3 py-2 text-sm font-medium text-[#a1a1aa] transition-colors hover:text-white"
            >
              {l.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {!isAuthenticated && (
            <Link
              to="/login"
              className="focus-ring hidden rounded-md px-3 py-2 text-sm font-medium text-[#d4d4d8] transition-colors hover:text-white sm:block"
            >
              Sign in
            </Link>
          )}
          <Link
            to="/dashboard"
            className="focus-ring group inline-flex items-center gap-1.5 rounded-lg bg-white px-3.5 py-2 text-sm font-semibold text-omnivra-bg-root transition-transform duration-200 hover:scale-[1.03] active:scale-95"
          >
            {isAuthenticated ? 'Open app' : 'Launch app'}
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" aria-hidden />
          </Link>
        </div>
      </nav>
    </motion.header>
  )
}
