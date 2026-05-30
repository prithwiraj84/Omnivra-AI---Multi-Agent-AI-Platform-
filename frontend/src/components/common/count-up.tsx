/**
 * CountUp — animates a numeric value string up from zero on mount.
 * Handles formatted values like "18", "24", "98.6%", "$0.18", "1,228". Falls back to the
 * literal string when it can't parse a number or when reduced motion is preferred.
 */
import { useEffect, useState } from 'react'
import { useReducedMotion } from 'framer-motion'

interface CountUpProps {
  value: string
  className?: string
  durationMs?: number
}

const NUMERIC = /^([^\d-]*)(-?[\d,]*\.?\d+)(.*)$/

export function CountUp({ value, className, durationMs = 900 }: CountUpProps) {
  const reduce = useReducedMotion()
  const match = value.match(NUMERIC)
  const target = match ? parseFloat(match[2].replace(/,/g, '')) : NaN
  const [display, setDisplay] = useState(reduce || !match ? target : 0)

  useEffect(() => {
    if (reduce || !match || Number.isNaN(target)) return
    let raf = 0
    let start = 0
    const step = (now: number) => {
      if (!start) start = now
      const t = Math.min(1, (now - start) / durationMs)
      const eased = 1 - Math.pow(1 - t, 3)
      setDisplay(target * eased)
      if (t < 1) raf = requestAnimationFrame(step)
      else setDisplay(target)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [target, durationMs, reduce, match])

  if (!match || Number.isNaN(target)) return <span className={className}>{value}</span>

  const prefix = match[1]
  const numStr = match[2].replace(/,/g, '')
  const suffix = match[3]
  const decimals = numStr.includes('.') ? numStr.split('.')[1].length : 0
  const shown = decimals > 0 ? display.toFixed(decimals) : Math.round(display).toLocaleString('en-US')

  return (
    <span className={className}>
      {prefix}
      {shown}
      {suffix}
    </span>
  )
}
