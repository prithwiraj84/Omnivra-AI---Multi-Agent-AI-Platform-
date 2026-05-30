import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'
import { NeonBadge } from '@/components/ui/neon-badge'

export interface DateTimeStatusProps {
  /** Extra classes for the outer wrapper. */
  className?: string
}

const TIME_OPTS: Intl.DateTimeFormatOptions = {
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: true,
}

const DATE_OPTS: Intl.DateTimeFormatOptions = {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
}

/**
 * DateTimeStatus — the right-aligned live clock/date block. A `setInterval`
 * ticks every second from the `Date` constructor (cleared on unmount), with a
 * big mono time, the long-form date, and an "All Systems Operational" badge.
 */
export function DateTimeStatus({ className }: DateTimeStatusProps) {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className={cn('flex flex-col items-start gap-1.5 sm:items-end', className)}>
      <span className="tabular font-mono text-2xl font-bold leading-none text-[#fafafa]">
        {now.toLocaleTimeString('en-US', TIME_OPTS)}
      </span>
      <span className="text-sm text-[#a1a1aa]">{now.toLocaleDateString('en-US', DATE_OPTS)}</span>
      <NeonBadge tone="success" dot>
        All Systems Operational
      </NeonBadge>
    </div>
  )
}
