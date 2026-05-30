import { motion, useReducedMotion } from 'framer-motion'

import { GlassCard } from '@/components/ui/glass-card'
import { Sparkline } from '@/components/ui/sparkline'
import { easeInOut } from '@/lib/motion'

export interface BrandFooterCardProps {
  tagline?: string
}

/** Static upward trend backing the brand sparkline. */
const TREND = [4, 6, 5, 8, 7, 11, 10, 14, 13, 18]

/**
 * BrandFooterCard — the bottom brand panel: a strong glass card with an ambient
 * violet/cyan radial glow, a violet→indigo gradient title "Omnivra AI Company OS",
 * a tagline subtitle, and a small violet sparkline trend on the right.
 */
export function BrandFooterCard({
  tagline = "The World's First AI Native Company OS",
}: BrandFooterCardProps) {
  const reduce = useReducedMotion()

  return (
    <GlassCard variant="strong" padding="lg" className="overflow-hidden">
      <div className="ambient-glow pointer-events-none absolute inset-0" aria-hidden />
      {/* Slow violet→cyan sheen drifting across the card — a quiet "alive" signal. */}
      {!reduce && (
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-omnivra-violet/10 to-transparent"
          initial={{ x: '-120%' }}
          animate={{ x: '120%' }}
          transition={{ duration: 6, ease: easeInOut, repeat: Infinity, repeatDelay: 2.5 }}
        />
      )}
      <div className="relative flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <h3 className="bg-gradient-to-r from-omnivra-violet to-omnivra-indigo bg-clip-text text-lg font-bold tracking-tight text-transparent">
            Omnivra AI Company OS
          </h3>
          <p className="mt-1 text-sm text-zinc-400">{tagline}</p>
        </div>
        <Sparkline data={TREND} accent="violet" width={120} height={36} className="shrink-0" />
      </div>
    </GlassCard>
  )
}
