/**
 * GenrePreview — a tiny, parametric SVG mock-up of a document GENRE's visual structure
 * (cover, columns, numbering, heading treatment, bullets, image). It mirrors the backend
 * StructureSpec's high-impact axes so the Document Studio gallery lets you pick a genre by
 * its LOOK, not just its name. Pure SVG, no assets; grayscale + one accent so it reads as a
 * set (it shows STRUCTURE, not color — the palette is the separate Theme control).
 */
import type { DocStyle } from '@/lib/api/types'

export type GenreCover =
  | 'band'
  | 'fullbleed'
  | 'centered'
  | 'letterhead'
  | 'masthead'
  | 'plain'
  | 'magazine'
  | 'hero'
  | 'inline'
export type GenreHeading = 'rule' | 'bar' | 'box' | 'kicker' | 'caps' | 'plain'
export type GenreBullet = 'dot' | 'dash' | 'tri' | 'arrow' | 'diamond' | 'check' | 'num' | 'none'

export interface GenreShape {
  /** Genre label (real-world document type) shown under the name. */
  genre: string
  cover: GenreCover
  columns: 1 | 2
  numbered: boolean
  heading: GenreHeading
  bullet: GenreBullet
  image: boolean
}

/** Per-style structural descriptor — mirrors backend STRUCTURE (high-impact axes only). */
export const GENRE_SHAPE: Record<DocStyle, GenreShape> = {
  professional: { genre: 'Corporate report', cover: 'band', columns: 1, numbered: false, heading: 'rule', bullet: 'dot', image: true },
  casual: { genre: 'Blog / zine', cover: 'plain', columns: 1, numbered: false, heading: 'plain', bullet: 'tri', image: true },
  academic: { genre: 'Journal article', cover: 'centered', columns: 2, numbered: true, heading: 'plain', bullet: 'dash', image: false },
  formal: { genre: 'Official memo', cover: 'letterhead', columns: 1, numbered: true, heading: 'caps', bullet: 'dash', image: false },
  informal: { genre: 'Notebook', cover: 'plain', columns: 1, numbered: false, heading: 'bar', bullet: 'dash', image: true },
  conversational: { genre: 'Q & A', cover: 'plain', columns: 1, numbered: false, heading: 'plain', bullet: 'arrow', image: true },
  technical: { genre: 'Manual / spec', cover: 'band', columns: 1, numbered: true, heading: 'bar', bullet: 'num', image: true },
  business: { genre: 'Executive briefing', cover: 'hero', columns: 1, numbered: false, heading: 'plain', bullet: 'dot', image: true },
  creative: { genre: 'Magazine feature', cover: 'magazine', columns: 2, numbered: false, heading: 'kicker', bullet: 'diamond', image: true },
  simple: { genre: 'Minimalist', cover: 'centered', columns: 1, numbered: false, heading: 'plain', bullet: 'dash', image: false },
  complex: { genre: 'Whitepaper', cover: 'centered', columns: 2, numbered: true, heading: 'plain', bullet: 'num', image: true },
  concise: { genre: 'One-pager brief', cover: 'inline', columns: 1, numbered: false, heading: 'rule', bullet: 'dot', image: false },
  detailed: { genre: 'Comprehensive doc', cover: 'band', columns: 1, numbered: true, heading: 'rule', bullet: 'dot', image: true },
  persuasive: { genre: 'Proposal / pitch', cover: 'band', columns: 1, numbered: false, heading: 'plain', bullet: 'arrow', image: true },
  informative: { genre: 'Newsletter', cover: 'masthead', columns: 2, numbered: false, heading: 'kicker', bullet: 'dot', image: true },
  neutral: { genre: 'Standards doc', cover: 'centered', columns: 1, numbered: true, heading: 'plain', bullet: 'dash', image: false },
  friendly: { genre: 'Brochure', cover: 'band', columns: 1, numbered: false, heading: 'box', bullet: 'check', image: true },
  'seo-friendly': { genre: 'Web article', cover: 'plain', columns: 1, numbered: false, heading: 'plain', bullet: 'check', image: true },
  marketing: { genre: 'Landing page', cover: 'fullbleed', columns: 1, numbered: false, heading: 'kicker', bullet: 'check', image: true },
  legal: { genre: 'Contract / brief', cover: 'letterhead', columns: 1, numbered: true, heading: 'caps', bullet: 'num', image: false },
}

const ACCENT = '#22d3ee'
const INK = '#9ca3af'
const FAINT = '#3f3f46'
const PAPER = '#0b0b0e'

/** A run of body "text" lines in a column starting at (x,y), `w` wide. */
function Lines({ x, y, w, n, gap = 4 }: { x: number; y: number; w: number; n: number; gap?: number }) {
  return (
    <>
      {Array.from({ length: n }).map((_, i) => (
        <rect
          key={i}
          x={x}
          y={y + i * gap}
          width={i === n - 1 ? w * 0.6 : w}
          height={1.4}
          rx={0.7}
          fill={FAINT}
        />
      ))}
    </>
  )
}

/** A bullet/numbered list of `n` items. */
function Bullets({ x, y, w, n, bullet }: { x: number; y: number; w: number; n: number; bullet: GenreBullet }) {
  return (
    <>
      {Array.from({ length: n }).map((_, i) => {
        const cy = y + i * 5
        const mark =
          bullet === 'num' ? (
            <text x={x} y={cy + 2.2} fontSize={3} fill={ACCENT}>
              {i + 1}.
            </text>
          ) : bullet === 'none' ? null : (
            <circle cx={x + 1} cy={cy + 1.4} r={bullet === 'diamond' ? 1.1 : 1} fill={ACCENT} />
          )
        return (
          <g key={i}>
            {mark}
            <rect x={x + 4} y={cy} width={w} height={1.4} rx={0.7} fill={FAINT} />
          </g>
        )
      })}
    </>
  )
}

/** Renders the cover/title region; returns the y where body content can begin. */
function Cover({ cover }: { cover: GenreCover }) {
  switch (cover) {
    case 'band':
      return (
        <>
          <rect x={0} y={0} width={80} height={16} fill={ACCENT} opacity={0.85} />
          <rect x={6} y={6} width={40} height={3} rx={1.5} fill={PAPER} />
        </>
      )
    case 'fullbleed':
      return (
        <>
          <rect x={0} y={0} width={80} height={42} fill={ACCENT} opacity={0.55} />
          <rect x={0} y={30} width={80} height={12} fill="#000" opacity={0.45} />
          <rect x={22} y={34} width={36} height={3} rx={1.5} fill="#fff" opacity={0.9} />
        </>
      )
    case 'magazine':
      return (
        <>
          <rect x={0} y={0} width={80} height={30} fill={ACCENT} opacity={0.55} />
          <rect x={6} y={33} width={14} height={2} rx={1} fill={ACCENT} />
          <rect x={6} y={37} width={46} height={3.5} rx={1.5} fill={INK} />
        </>
      )
    case 'centered':
      return (
        <>
          <rect x={20} y={10} width={40} height={3.4} rx={1.7} fill={INK} />
          <rect x={32} y={16} width={16} height={1.4} rx={0.7} fill={ACCENT} />
          <rect x={26} y={20} width={28} height={1.6} rx={0.8} fill={FAINT} />
        </>
      )
    case 'letterhead':
      return (
        <>
          <rect x={0} y={0} width={80} height={2.5} fill={ACCENT} />
          <rect x={6} y={6} width={26} height={2} rx={1} fill={INK} />
          <line x1={6} y1={11} x2={74} y2={11} stroke={FAINT} strokeWidth={0.5} />
          <rect x={6} y={15} width={40} height={3} rx={1.5} fill={INK} />
        </>
      )
    case 'masthead':
      return (
        <>
          <line x1={4} y1={5} x2={76} y2={5} stroke={INK} strokeWidth={0.8} />
          <rect x={20} y={8} width={40} height={4} rx={2} fill={INK} />
          <line x1={4} y1={15} x2={76} y2={15} stroke={INK} strokeWidth={0.8} />
        </>
      )
    case 'hero':
      return (
        <>
          <rect x={0} y={0} width={4} height={22} fill={ACCENT} />
          <rect x={8} y={6} width={46} height={4} rx={2} fill={INK} />
          <rect x={8} y={13} width={30} height={1.6} rx={0.8} fill={FAINT} />
        </>
      )
    case 'inline':
      return (
        <>
          <rect x={6} y={6} width={40} height={2.6} rx={1.3} fill={ACCENT} />
          <line x1={6} y1={12} x2={74} y2={12} stroke={ACCENT} strokeWidth={0.5} />
        </>
      )
    default: // plain
      return (
        <>
          <rect x={6} y={6} width={52} height={5} rx={2.5} fill={INK} />
          <rect x={6} y={14} width={30} height={1.6} rx={0.8} fill={FAINT} />
        </>
      )
  }
}

/** A section heading mark in one of the genre's heading styles. */
function Heading({ x, y, w, heading, numbered, idx }: { x: number; y: number; w: number; heading: GenreHeading; numbered: boolean; idx: number }) {
  const label = (
    <rect x={heading === 'bar' ? x + 4 : x} y={y} width={w} height={2.6} rx={1.3} fill={INK} />
  )
  return (
    <g>
      {numbered && (
        <text x={x - 4} y={y + 2.4} fontSize={3} fill={ACCENT}>
          {idx}
        </text>
      )}
      {heading === 'bar' && <rect x={x} y={y - 0.3} width={1.4} height={3.2} fill={ACCENT} />}
      {heading === 'box' && <rect x={x - 1.5} y={y - 1.5} width={w + 3} height={5.6} rx={1} fill="none" stroke={ACCENT} strokeWidth={0.5} />}
      {heading === 'kicker' && <rect x={x} y={y - 3} width={10} height={1.4} rx={0.7} fill={ACCENT} />}
      {label}
      {heading === 'rule' && <line x1={x} y1={y + 4} x2={x + w + 6} y2={y + 4} stroke={ACCENT} strokeWidth={0.5} />}
    </g>
  )
}

/**
 * Render the mini-mockup for a genre. `selected` brightens the accent + border.
 */
export function GenrePreview({ shape, selected = false, className }: { shape: GenreShape; selected?: boolean; className?: string }) {
  const bodyTop = 24
  const cols = shape.columns
  return (
    <svg viewBox="0 0 80 100" className={className} role="img" aria-label={`${shape.genre} layout`} preserveAspectRatio="xMidYMid meet">
      <rect x={0} y={0} width={80} height={100} rx={2} fill={PAPER} stroke={selected ? ACCENT : FAINT} strokeWidth={selected ? 1 : 0.5} />
      <Cover cover={shape.cover} />
      {/* first section */}
      <Heading x={8} y={bodyTop} w={34} heading={shape.heading} numbered={shape.numbered} idx={1} />
      {cols === 2 ? (
        <>
          <Lines x={8} y={bodyTop + 7} w={28} n={5} />
          <Lines x={44} y={bodyTop + 7} w={28} n={5} />
        </>
      ) : (
        <Lines x={8} y={bodyTop + 7} w={64} n={3} />
      )}
      {/* second section */}
      <Heading x={8} y={bodyTop + 32} w={30} heading={shape.heading} numbered={shape.numbered} idx={2} />
      {shape.bullet !== 'none' && shape.bullet !== 'dash' ? (
        <Bullets x={8} y={bodyTop + 39} w={48} n={3} bullet={shape.bullet} />
      ) : (
        <Lines x={8} y={bodyTop + 39} w={64} n={3} />
      )}
      {shape.image && <rect x={8} y={bodyTop + 56} width={shape.cover === 'fullbleed' ? 64 : 30} height={16} rx={1.5} fill={ACCENT} opacity={0.25} stroke={ACCENT} strokeWidth={0.4} />}
    </svg>
  )
}
