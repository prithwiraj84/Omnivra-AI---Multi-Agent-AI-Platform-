/**
 * CountUp — animates a numeric value string toward its target.
 * Handles formatted values like "18", "24", "98.6%", "$0.18", "1,228". Falls back to the
 * literal string when it can't parse a number or when reduced motion is preferred.
 *
 * The animation effect depends ONLY on stable primitives (the parsed `target` number, duration,
 * reduced-motion). It must NOT depend on the `match` array — that is a fresh object every render,
 * which would re-run the effect and reset the counter to ~0 on every re-render (charts, polling,
 * framer-motion), making every stat read 0. It animates from the LAST shown value to the new
 * target, so a polled update counts smoothly instead of snapping back to zero.
 */
import { useEffect, useRef, useState } from 'react'
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
  const animatable = !!match && !Number.isNaN(target)
  const [display, setDisplay] = useState(animatable && !reduce ? 0 : target)
  const fromRef = useRef(0) // last shown value, so updates tween from here (not from 0)

  useEffect(() => {
    if (!animatable || reduce) {
      setDisplay(target)
      fromRef.current = animatable ? target : 0
      return
    }
    const from = fromRef.current
    let raf = 0
    let start = 0
    const step = (now: number) => {
      if (!start) start = now
      const t = Math.min(1, (now - start) / durationMs)
      const eased = 1 - Math.pow(1 - t, 3)
      const v = from + (target - from) * eased
      setDisplay(v)
      fromRef.current = v
      if (t < 1) {
        raf = requestAnimationFrame(step)
      } else {
        setDisplay(target)
        fromRef.current = target
      }
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
    // Stable primitive deps only — re-run when the TARGET changes, never on every render.
  }, [target, durationMs, reduce, animatable])

  if (!animatable) return <span className={className}>{value}</span>

  const prefix = match![1]
  const numStr = match![2].replace(/,/g, '')
  const suffix = match![3]
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
