/**
 * Omnivra Design Tokens — single source of truth for JavaScript consumers.
 *
 * CSS owns styling via `src/index.css` + `tailwind.config.ts`. This file mirrors the same
 * values for code that needs literal JS colors (Recharts, Framer Motion, React Flow), so the
 * charts and the CSS never drift. See `docs/DESIGN_SYSTEM.md` for the authoritative spec.
 */

/** Background / surface layers. */
export const bg = {
  root: '#070a0f',
  base: '#0a0a0f',
  sidebar: '#0a0e16',
  topbar: '#080c14',
  surface1: '#0c1018',
  surface2: '#11151f',
  surface3: '#161b27',
} as const

/** The four signature neon accents (+ supporting hues). */
export const accent = {
  cyan: '#22d3ee',
  cyanDim: '#0e7490',
  violet: '#a855f7',
  violetAlt: '#8b5cf6',
  indigo: '#6366f1',
  blue: '#3b82f6',
  emerald: '#10b981',
  emeraldBright: '#34d399',
  amber: '#f59e0b',
  red: '#ef4444',
  pink: '#ec4899',
} as const

/** Semantic colors. */
export const semantic = {
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
} as const

/** Text ramp (zinc-derived). */
export const text = {
  primary: '#fafafa',
  secondary: '#e4e4e7',
  muted: '#a1a1aa',
  faint: '#71717a',
  label: '#52525b',
  onAccent: '#06060a',
} as const

/** Border / divider alphas (white over dark). */
export const border = {
  subtle: 'rgba(255,255,255,0.06)',
  default: 'rgba(255,255,255,0.08)',
  strong: 'rgba(255,255,255,0.12)',
  neon: 'rgba(34,211,238,0.35)',
} as const

/**
 * Recharts area-chart series for "Task Execution Overview".
 * Each series provides a stroke and a top→bottom gradient fill.
 */
export const areaSeries = {
  completed: { stroke: '#10b981', gradientTop: 'rgba(16,185,129,0.35)', gradientBottom: 'rgba(16,185,129,0)' },
  inProgress: { stroke: '#3b82f6', gradientTop: 'rgba(59,130,246,0.30)', gradientBottom: 'rgba(59,130,246,0)' },
  failed: { stroke: '#ef4444', gradientTop: 'rgba(239,68,68,0.25)', gradientBottom: 'rgba(239,68,68,0)' },
} as const

/** Ordered categorical palette for the donut (Task Distribution) + usage bars. */
export const categorical = [
  '#22d3ee', // cyan
  '#a855f7', // violet
  '#3b82f6', // blue
  '#f59e0b', // amber
  '#10b981', // emerald
  '#ec4899', // pink
  '#8b5cf6', // violet-alt
] as const

/** Chart surface helpers. */
export const chart = {
  donutTrack: 'rgba(255,255,255,0.04)',
  barTrack: 'rgba(255,255,255,0.06)',
  grid: 'rgba(255,255,255,0.06)',
  axis: '#71717a',
  tooltipBg: '#11151f',
  tooltipBorder: 'rgba(255,255,255,0.10)',
} as const

/** Border radii (px). */
export const radius = { sm: 8, md: 12, lg: 16, xl: 20, full: 9999 } as const

/** Backdrop blur levels (px). */
export const blur = { sm: 8, md: 12, lg: 20 } as const

/** Layout dimensions (px). */
export const layout = {
  sidebarWidth: 248,
  topbarHeight: 60,
  rightRailWidth: 320,
  contentMax: 1600,
  gutter: 24,
} as const

/** Framer Motion tokens. */
export const motion = {
  duration: { fast: 0.15, base: 0.22, slow: 0.35, xslow: 0.6 },
  ease: {
    out: [0.22, 1, 0.36, 1] as [number, number, number, number],
    inOut: [0.4, 0, 0.2, 1] as [number, number, number, number],
  },
  spring: { type: 'spring' as const, stiffness: 320, damping: 30 },
  stagger: 0.05,
} as const

/** Accent palette type + the canonical four families used across components. */
export type Accent = 'cyan' | 'violet' | 'blue' | 'emerald' | 'amber' | 'pink'

/** Department → accent mapping (keeps agent cards color-coded consistently). */
export const departmentAccent: Record<string, Accent> = {
  Executive: 'cyan',
  Architecture: 'violet',
  Design: 'pink',
  Engineering: 'blue',
  'Quality & Security': 'emerald',
  Marketing: 'amber',
  Documentation: 'violet',
  Recovery: 'amber',
  'System Ops': 'cyan',
  Media: 'emerald',
}

/** Hex lookup for a named accent (for JS consumers like Recharts/React Flow). */
export const accentHex: Record<Accent, string> = {
  cyan: accent.cyan,
  violet: accent.violet,
  blue: accent.blue,
  emerald: accent.emerald,
  amber: accent.amber,
  pink: accent.pink,
}

export const tokens = {
  bg,
  accent,
  semantic,
  text,
  border,
  areaSeries,
  categorical,
  chart,
  radius,
  blur,
  layout,
  motion,
  departmentAccent,
  accentHex,
}

export default tokens
