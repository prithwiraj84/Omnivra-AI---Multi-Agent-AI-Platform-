/**
 * The Omnivra brand mark — a multi-agent "nexus": an orchestrator core ringed by four agent
 * nodes on connecting spokes. One glyph, used everywhere (sidebar, landing nav, footer, product
 * mockup, favicon) so the brand reads consistently at every size.
 *
 *  - <OmnivraMark />  the glyph alone, inheriting `currentColor` — drop it inside an existing
 *                     gradient tile (that's how the app chrome uses it).
 *  - <OmnivraLogo />  the full lockup: gradient tile + glyph, self-contained.
 *
 * Geometry is tuned for legibility at 16px: bold nodes, thick spokes, generous padding, and
 * perfect 4-fold symmetry so it never looks optically off-centre.
 */
import { useId } from 'react'

import { cn } from '@/lib/utils'

/** Node centres at 45° on a radius-9 orbit (a 32×32 viewBox, centred on 16,16). */
const NODES: [number, number][] = [
  [22.36, 9.64], // NE
  [22.36, 22.36], // SE
  [9.64, 22.36], // SW
  [9.64, 9.64], // NW
]

/**
 * The glyph only — inherits `currentColor`, so it drops into any coloured tile.
 * Decorative by default; pass a `title` to expose it to assistive tech.
 */
export function OmnivraMark({ className, title }: { className?: string; title?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={cn('h-5 w-5', className)}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      {title && <title>{title}</title>}
      {/* spokes: the delegation links from the core out to each agent */}
      <g stroke="currentColor" strokeWidth={2.2} strokeLinecap="round">
        {NODES.map(([x, y]) => (
          <line key={`${x}-${y}`} x1={16} y1={16} x2={x} y2={y} />
        ))}
      </g>
      <g fill="currentColor">
        {/* agent nodes */}
        {NODES.map(([x, y]) => (
          <circle key={`${x}-${y}`} cx={x} cy={y} r={2.8} />
        ))}
        {/* orchestrator core */}
        <circle cx={16} cy={16} r={4.5} />
      </g>
    </svg>
  )
}

/**
 * The full lockup: a gradient tile with the glyph knocked out in the app's near-black, matching
 * the favicon exactly. The gradient id is `useId`-scoped so multiple logos on one page never
 * collide.
 */
export function OmnivraLogo({ className, title = 'Omnivra' }: { className?: string; title?: string }) {
  const gid = useId()
  return (
    <svg viewBox="0 0 32 32" className={cn('h-10 w-10', className)} role="img" aria-label={title}>
      <title>{title}</title>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#22d3ee" />
          <stop offset="0.5" stopColor="#6366f1" />
          <stop offset="1" stopColor="#a855f7" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8.5" fill={`url(#${gid})`} />
      <g stroke="#0a0a0f" strokeWidth={2.2} strokeLinecap="round">
        {NODES.map(([x, y]) => (
          <line key={`${x}-${y}`} x1={16} y1={16} x2={x} y2={y} />
        ))}
      </g>
      <g fill="#0a0a0f">
        {NODES.map(([x, y]) => (
          <circle key={`${x}-${y}`} cx={x} cy={y} r={2.8} />
        ))}
        <circle cx={16} cy={16} r={4.5} />
      </g>
    </svg>
  )
}
