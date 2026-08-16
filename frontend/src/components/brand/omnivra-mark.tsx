/**
 * The Omnivra brand mark — the ringed "O" orb of the Omnivra logo: a bold O core, an orbit ring
 * sweeping around it, and agent nodes riding that orbit. One glyph everywhere (sidebar, landing
 * nav, footer, product mockup, favicon) so the brand reads consistently at every size.
 *
 *  - <OmnivraMark />  the glyph alone, inheriting `currentColor` — drop it inside an existing
 *                     gradient tile (that's how the app chrome uses it).
 *  - <OmnivraLogo />  the full lockup: gradient tile + glyph, self-contained.
 *
 * Drawn as vectors rather than shipping the raster logo because this renders at 16px in a
 * browser tab: a downscaled photo-real render turns to mush there, while a stroked O with three
 * orbit nodes stays legible. The raster stays the SOCIAL card (og:image), where it shines.
 *
 * The orbit is an ellipse rotated -20°, matching the logo's tilt. Nodes sit ON that ellipse, so
 * the ring reads as depth rather than decoration.
 */
import { useId } from 'react'

import { cn } from '@/lib/utils'

/** Agent nodes, positioned on the tilted orbit (32×32 viewBox centred on 16,16). */
const NODES: [number, number][] = [
  [4.6, 11.9], // west, above the ring line
  [27.4, 20.1], // east, below it
  [16, 4.2], // north — the orchestrator's own node
]
/** The orbit: rx/ry of the tilted ellipse the nodes ride. */
const ORBIT = { rx: 13.4, ry: 5.2, rotate: -20 }
/** The O core. Stroked (not filled) so the counter stays open and readable at 16px. */
const CORE = { r: 7.2, width: 3.6 }

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
      {/* orbit ring — lighter than the core so the O stays the subject */}
      <ellipse
        cx={16}
        cy={16}
        rx={ORBIT.rx}
        ry={ORBIT.ry}
        transform={`rotate(${ORBIT.rotate} 16 16)`}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.7}
        opacity={0.55}
      />
      {/* the O core */}
      <circle cx={16} cy={16} r={CORE.r} fill="none" stroke="currentColor" strokeWidth={CORE.width} />
      {/* agent nodes riding the orbit */}
      <g fill="currentColor">
        {NODES.map(([x, y]) => (
          <circle key={`${x}-${y}`} cx={x} cy={y} r={2.5} />
        ))}
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
      <ellipse
        cx={16}
        cy={16}
        rx={ORBIT.rx}
        ry={ORBIT.ry}
        transform={`rotate(${ORBIT.rotate} 16 16)`}
        fill="none"
        stroke="#0a0a0f"
        strokeWidth={1.7}
        opacity={0.6}
      />
      <circle cx={16} cy={16} r={CORE.r} fill="none" stroke="#0a0a0f" strokeWidth={CORE.width} />
      <g fill="#0a0a0f">
        {NODES.map(([x, y]) => (
          <circle key={`${x}-${y}`} cx={x} cy={y} r={2.5} />
        ))}
      </g>
    </svg>
  )
}
