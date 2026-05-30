import { forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import { accentClasses } from '@/lib/accents'
import type { Accent } from '@/types'

/**
 * GlassCard — the base surface for every Omnivra card/panel.
 *  - `glass` (default): translucent blur card (stat/agent/approval/media cards).
 *  - `strong`: heavier glass (modals/popovers).
 *  - `panel`: opaque surface (chart containers — blur over moving charts is wasteful).
 * `glow` adds a neon ring: a hover glow when `interactive`, else an always-on glow.
 */
const glassCardVariants = cva('relative', {
  variants: {
    variant: {
      glass: 'glass-card',
      strong: 'glass-strong',
      panel: 'panel',
    },
    padding: { none: '', sm: 'p-3', md: 'p-5', lg: 'p-6' },
    interactive: {
      true: 'cursor-pointer transition-all duration-200 ease-out-quint hover:-translate-y-0.5 hover:border-white/15',
      false: '',
    },
  },
  defaultVariants: { variant: 'glass', padding: 'md', interactive: false },
})

// Literal hover classes so Tailwind's scanner emits them.
const glowHover: Record<Accent, string> = {
  cyan: 'hover:shadow-glow-cyan',
  violet: 'hover:shadow-glow-violet',
  blue: 'hover:shadow-glow-blue',
  emerald: 'hover:shadow-glow-emerald',
  amber: '',
  pink: '',
}

export interface GlassCardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof glassCardVariants> {
  glow?: Accent
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant, padding, interactive, glow, ...props }, ref) => {
    const glowClass = glow ? (interactive ? glowHover[glow] : accentClasses(glow).glow) : ''
    return (
      <div
        ref={ref}
        className={cn(glassCardVariants({ variant, padding, interactive }), glowClass, className)}
        {...props}
      />
    )
  },
)
GlassCard.displayName = 'GlassCard'

export { glassCardVariants }
