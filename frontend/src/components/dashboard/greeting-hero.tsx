import { motion, useReducedMotion } from 'framer-motion'

import { DateTimeStatus } from '@/components/dashboard/date-time-status'
import { RunTask } from '@/components/dashboard/run-task'
import { Reveal } from '@/components/common/reveal'

export interface GreetingHeroProps {
  /** Name shown in the greeting (defaults to the company name). */
  name?: string
}

/**
 * GreetingHero — the page header. LEFT: a large greeting + subtitle sitting on
 * a subtle ambient radial glow; RIGHT: the live `DateTimeStatus` clock block.
 * Stacks on small screens, splits into a row from `sm` up.
 */
export function GreetingHero({ name = 'Omnivra' }: GreetingHeroProps) {
  const reduce = useReducedMotion()

  return (
    <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
      <div className="ambient-glow pointer-events-none absolute -inset-x-6 -inset-y-8 -z-10 rounded-3xl" />

      <Reveal className="flex flex-col gap-1.5">
        <h1 className="text-2xl font-bold tracking-tight text-[#fafafa] sm:text-3xl">
          Good morning, {name}!{' '}
          <motion.span
            aria-hidden
            className="inline-block origin-[70%_80%]"
            animate={reduce ? undefined : { rotate: [0, 16, -8, 16, 0] }}
            transition={
              reduce ? undefined : { duration: 1.6, ease: 'easeInOut', repeat: Infinity, repeatDelay: 2.4 }
            }
          >
            👋
          </motion.span>
        </h1>
        <p className="text-sm text-[#a1a1aa] sm:text-base">
          Your AI Company is running at full capacity.
        </p>

        <RunTask />
      </Reveal>

      <DateTimeStatus className="shrink-0" />
    </div>
  )
}
