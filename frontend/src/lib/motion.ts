/**
 * Shared Framer Motion variants + transitions, derived from the design motion tokens
 * (docs/DESIGN_SYSTEM.md §6). Consume via the `<Reveal>` / `<Stagger>` helpers, which
 * also gate everything behind `useReducedMotion()`.
 */
import type { Transition, Variants } from 'framer-motion'
import { motion as motionTokens } from '@/styles/tokens'

export const easeOut = motionTokens.ease.out
export const easeInOut = motionTokens.ease.inOut

export const tBase: Transition = { duration: motionTokens.duration.base, ease: easeOut }
export const tSlow: Transition = { duration: motionTokens.duration.slow, ease: easeOut }

/** Fade + rise — the default entrance for cards, rows and sections. */
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: easeOut } },
}

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: motionTokens.duration.slow, ease: easeOut } },
}

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  show: { opacity: 1, scale: 1, transition: { duration: motionTokens.duration.slow, ease: easeOut } },
}

/** Parent that staggers its children's entrance. Pair with `staggerItem`. */
export const staggerContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: motionTokens.stagger, delayChildren: 0.04 } },
}

export const staggerItem: Variants = fadeUp

/** Interactive-card hover: lift slightly. Combine with a glow class on the element. */
export const cardHover = { y: -3, transition: tBase } as const

/** Route-transition variants for the animated <Outlet/>. */
export const pageTransition: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: easeOut } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.18, ease: easeInOut } },
}
