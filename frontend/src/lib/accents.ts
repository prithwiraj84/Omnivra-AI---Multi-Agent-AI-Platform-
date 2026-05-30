/**
 * Accent → Tailwind class maps. Single place that turns a semantic accent
 * (`cyan`, `violet`, …) into the concrete classes defined in `tailwind.config.ts`
 * and `src/index.css`. Components never hardcode accent classes — they call these.
 */
import type { Accent } from '@/styles/tokens'

export interface AccentClasses {
  /** Tinted icon-tile background + icon color (`.tile-*` from index.css). */
  tile: string
  /** Accent text color (omnivra namespace). */
  text: string
  /** Status-dot / glyph color. */
  dot: string
  /** Hover/active neon glow box-shadow (empty for amber/pink). */
  glow: string
  /** Subtle accent-tinted border. */
  border: string
}

const MAP: Record<Accent, AccentClasses> = {
  cyan: {
    tile: 'tile-cyan',
    text: 'text-omnivra-cyan',
    dot: 'text-omnivra-cyan',
    glow: 'shadow-glow-cyan',
    border: 'border-omnivra-cyan/30',
  },
  violet: {
    tile: 'tile-violet',
    text: 'text-omnivra-purple',
    dot: 'text-omnivra-purple',
    glow: 'shadow-glow-violet',
    border: 'border-omnivra-purple/30',
  },
  blue: {
    tile: 'tile-blue',
    text: 'text-omnivra-blue',
    dot: 'text-omnivra-blue',
    glow: 'shadow-glow-blue',
    border: 'border-omnivra-blue/30',
  },
  emerald: {
    tile: 'tile-emerald',
    text: 'text-omnivra-emerald',
    dot: 'text-omnivra-emerald',
    glow: 'shadow-glow-emerald',
    border: 'border-omnivra-emerald/30',
  },
  amber: {
    tile: 'tile-amber',
    text: 'text-omnivra-amber',
    dot: 'text-omnivra-amber',
    glow: '',
    border: 'border-omnivra-amber/30',
  },
  pink: {
    tile: 'tile-pink',
    text: 'text-omnivra-pink',
    dot: 'text-omnivra-pink',
    glow: '',
    border: 'border-omnivra-pink/30',
  },
}

export function accentClasses(accent: Accent): AccentClasses {
  return MAP[accent] ?? MAP.cyan
}

/** Tone (semantic) → NeonBadge variant class (from index.css `.badge-*`). */
export const toneBadgeClass: Record<string, string> = {
  success: 'badge-success',
  info: 'badge-info',
  warning: 'badge-warning',
  danger: 'badge-danger',
  cyan: 'badge-cyan',
  violet: 'badge-violet',
  neutral: 'badge-info',
}
