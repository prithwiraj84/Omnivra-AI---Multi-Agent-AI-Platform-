/**
 * Motion helpers — entrance + stagger wrappers, all reduced-motion aware.
 *  - <Reveal>: fade-up an element on mount (optional delay).
 *  - <Stagger> + <StaggerItem>: a container that cascades its children in.
 * When the user prefers reduced motion, these render a plain <div> with no animation.
 */
import type { PropsWithChildren } from 'react'
import { motion, useReducedMotion } from 'framer-motion'

import { easeOut, staggerContainer, staggerItem } from '@/lib/motion'

interface RevealProps {
  className?: string
  /** Entrance delay in seconds. */
  delay?: number
  /** Vertical offset to rise from (px). */
  y?: number
}

export function Reveal({ children, className, delay = 0, y = 14 }: PropsWithChildren<RevealProps>) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: easeOut, delay }}
    >
      {children}
    </motion.div>
  )
}

export function Stagger({ children, className }: PropsWithChildren<{ className?: string }>) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>
  return (
    <motion.div className={className} variants={staggerContainer} initial="hidden" animate="show">
      {children}
    </motion.div>
  )
}

export function StaggerItem({ children, className }: PropsWithChildren<{ className?: string }>) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>
  return (
    <motion.div className={className} variants={staggerItem}>
      {children}
    </motion.div>
  )
}
