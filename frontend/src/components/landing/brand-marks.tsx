/**
 * Brand marks for the landing page — small, self-contained SVG logos of the platforms and
 * providers Omnivra integrates with. Accurate paths where they're simple and iconic (React,
 * Gemini, Supabase, Tailwind, YouTube, X, …); tasteful brand-colored monogram tiles for marks
 * that don't reduce well to a tiny inline path. All are decorative (aria-hidden) — the
 * surrounding tile carries the accessible name.
 */
import { useId } from 'react'

import { cn } from '@/lib/utils'

type MarkProps = { className?: string }

const S = 'h-6 w-6' // default mark size

export function ReactMark({ className }: MarkProps) {
  return (
    <svg viewBox="-11.5 -10.23 23 20.46" className={cn(S, className)} aria-hidden>
      <circle r="2.05" fill="#61DAFB" />
      <g stroke="#61DAFB" strokeWidth="1" fill="none">
        <ellipse rx="11" ry="4.2" />
        <ellipse rx="11" ry="4.2" transform="rotate(60)" />
        <ellipse rx="11" ry="4.2" transform="rotate(120)" />
      </g>
    </svg>
  )
}

export function GeminiMark({ className }: MarkProps) {
  const id = useId()
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#4285F4" />
          <stop offset="100%" stopColor="#9B72CB" />
        </linearGradient>
      </defs>
      <path
        fill={`url(#${id})`}
        d="M12 1.5c.7 5.8 4.7 9.8 10.5 10.5C16.7 12.7 12.7 16.7 12 22.5 11.3 16.7 7.3 12.7 1.5 12 7.3 11.3 11.3 7.3 12 1.5z"
      />
    </svg>
  )
}

export function SupabaseMark({ className }: MarkProps) {
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <path
        fill="#3ECF8E"
        d="M13.35 21.6c-.5.63-1.53.28-1.54-.53L11.7 13.2H4.9c-1.25 0-1.94-1.44-1.16-2.41l6.9-8.39c.5-.63 1.53-.28 1.54.53l.11 7.87h6.8c1.25 0 1.95 1.44 1.17 2.41l-6.91 8.39z"
      />
    </svg>
  )
}

export function FastAPIMark({ className }: MarkProps) {
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <circle cx="12" cy="12" r="10.5" fill="#009688" />
      <path fill="#fff" d="M13.2 4.8 6.6 13h4.2L10.6 19.2 17.3 11h-4.3l.2-6.2z" />
    </svg>
  )
}

export function TailwindMark({ className }: MarkProps) {
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <path
        fill="#38BDF8"
        d="M12 6c-2.67 0-4.33 1.33-5 4 1-1.33 2.17-1.83 3.5-1.5.76.19 1.31.74 1.91 1.35.98 1 2.11 2.15 4.59 2.15 2.67 0 4.33-1.33 5-4-1 1.33-2.17 1.83-3.5 1.5-.76-.19-1.31-.74-1.91-1.35C15.61 7.15 14.48 6 12 6zM7 12c-2.67 0-4.33 1.33-5 4 1-1.33 2.17-1.83 3.5-1.5.76.19 1.31.74 1.91 1.35.98 1 2.11 2.15 4.59 2.15 2.67 0 4.33-1.33 5-4-1 1.33-2.17 1.83-3.5 1.5-.76-.19-1.31-.74-1.91-1.35C10.61 13.15 9.48 12 7 12z"
      />
    </svg>
  )
}

export function HuggingFaceMark({ className }: MarkProps) {
  // The HF brand mark IS the hugging-face emoji — the most recognizable rendition at tiny sizes.
  return (
    <span className={cn('grid place-items-center text-lg leading-none', className)} aria-hidden>
      🤗
    </span>
  )
}

export function GoogleGMark({ className }: MarkProps) {
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.24 1.5-1.7 4.4-5.5 4.4-3.3 0-6-2.7-6-6.1s2.7-6.1 6-6.1c1.9 0 3.2.8 3.9 1.5l2.7-2.6C16.9 3 14.7 2 12 2 6.9 2 2.8 6.1 2.8 12S6.9 22 12 22c6.1 0 8.4-4.3 8.4-6.5 0-.4 0-.7-.1-1.1H12z" />
      <path fill="#4285F4" d="M21.9 14.4c.1-.4.1-.9.1-1.4 0-.5 0-.8-.1-1.1H12v3.9h5.5c-.1.8-.6 1.9-1.5 2.6l2.7 2.1c1.6-1.5 2.6-3.7 3.2-6.1z" />
      <path fill="#FBBC05" d="M6 14.3c-.2-.6-.3-1.2-.3-1.9s.1-1.3.3-1.9L3.3 8.4C2.6 9.7 2.2 11.3 2.2 12.9s.4 3.2 1.1 4.5L6 14.3z" />
      <path fill="#34A853" d="M12 22c2.4 0 4.5-.8 6-2.2l-2.7-2.1c-.8.5-1.8.9-3.3.9-2.5 0-4.6-1.7-5.4-4L3.9 16.6C5.3 19.8 8.4 22 12 22z" />
    </svg>
  )
}

export function LangGraphMark({ className }: MarkProps) {
  // A small directed graph — nodes + edges, the shape of a LangGraph workflow.
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <g stroke="#34d399" strokeWidth="1.4" fill="none">
        <path d="M6.5 6.5 12 12l5.5-5.5M12 12v6.5" />
      </g>
      <circle cx="6.5" cy="5.5" r="2.4" fill="#34d399" />
      <circle cx="17.5" cy="5.5" r="2.4" fill="#22d3ee" />
      <circle cx="12" cy="12" r="2.6" fill="#a855f7" />
      <circle cx="12" cy="19" r="2.2" fill="#38bdf8" />
    </svg>
  )
}

export function YouTubeMark({ className }: MarkProps) {
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <rect x="1.5" y="5" width="21" height="14" rx="3.5" fill="#FF0000" />
      <path fill="#fff" d="M10 9v6l5.2-3L10 9z" />
    </svg>
  )
}

export function InstagramMark({ className }: MarkProps) {
  const id = useId()
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <defs>
        <linearGradient id={id} x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stopColor="#FD5949" />
          <stop offset="50%" stopColor="#D6249F" />
          <stop offset="100%" stopColor="#8134AF" />
        </linearGradient>
      </defs>
      <rect x="2.5" y="2.5" width="19" height="19" rx="5.5" fill="none" stroke={`url(#${id})`} strokeWidth="2" />
      <circle cx="12" cy="12" r="4.4" fill="none" stroke={`url(#${id})`} strokeWidth="2" />
      <circle cx="17.4" cy="6.6" r="1.4" fill={`url(#${id})`} />
    </svg>
  )
}

export function LinkedInMark({ className }: MarkProps) {
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <rect x="2" y="2" width="20" height="20" rx="3" fill="#0A66C2" />
      <path
        fill="#fff"
        d="M7.1 9.2H4.6V19h2.5V9.2zM5.85 8.1a1.55 1.55 0 1 0 0-3.1 1.55 1.55 0 0 0 0 3.1zM19.4 13.6c0-2.9-1.55-4.6-3.9-4.6-1.4 0-2.3.7-2.7 1.5V9.2h-2.5V19h2.5v-5c0-1.3.6-2.2 1.8-2.2 1.1 0 1.6.8 1.6 2.2v5h2.5v-5.4z"
      />
    </svg>
  )
}

export function XMark({ className }: MarkProps) {
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <path
        fill="currentColor"
        d="M17.7 3H21l-7.3 8.3L22.2 21h-6.6l-5-6.1L4.9 21H1.6l7.8-8.9L1.4 3h6.8l4.5 5.6L17.7 3zm-1.2 16h1.8L6.9 4.9H5L16.5 19z"
      />
    </svg>
  )
}

export function FacebookMark({ className }: MarkProps) {
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <circle cx="12" cy="12" r="10.5" fill="#1877F2" />
      <path fill="#fff" d="M15.6 12.6h-2.4V20h-3v-7.4H8.3V10h1.9V8.4c0-2 1.2-3.4 3.4-3.4l2.1.1v2.5h-1.4c-.8 0-1.1.4-1.1 1.1V10h2.7l-.3 2.6z" />
    </svg>
  )
}

/** Brand-colored monogram tile for marks that don't reduce well to a tiny path. */
export function MonogramMark({
  label,
  color,
  className,
}: {
  label: string
  color: string
  className?: string
}) {
  return (
    <span
      className={cn(S, 'grid place-items-center rounded-md text-[11px] font-black leading-none text-white', className)}
      style={{ backgroundColor: color }}
      aria-hidden
    >
      {label}
    </span>
  )
}

export const OpenRouterMark = ({ className }: MarkProps) => (
  <MonogramMark label="OR" color="#7C6BF0" className={className} />
)
export const GroqMark = ({ className }: MarkProps) => (
  <MonogramMark label="G" color="#F55036" className={className} />
)
export const PexelsMark = ({ className }: MarkProps) => (
  <MonogramMark label="P" color="#05A081" className={className} />
)
export const ViteMark = ({ className }: MarkProps) => {
  const id = useId()
  return (
    <svg viewBox="0 0 24 24" className={cn(S, className)} aria-hidden>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#41D1FF" />
          <stop offset="100%" stopColor="#BD34FE" />
        </linearGradient>
      </defs>
      <path fill={`url(#${id})`} d="M22.2 4.1 12.6 21.4c-.25.44-.88.45-1.13 0L1.8 4.1c-.28-.5.16-1.1.72-1L12 4.9l9.47-1.8c.56-.1 1 .5.73 1z" />
      <path fill="#FFEA83" d="M15.7 2.9 12 3.6 8.6 3c-.1.4 0 .9.4 1.2l2.5 9.4c.1.4.7.4.8 0l.5-2.6 1.7-.4c.4-.1.5-.6.2-.9l-1-1 2.3-4.7c.2-.5-.1-1-.7-1.1z" opacity="0.95" />
    </svg>
  )
}

/** One integration tile: mark + name, glass surface with a hover lift. */
export function LogoTile({ mark, name, sub }: { mark: React.ReactNode; name: string; sub?: string }) {
  return (
    <div className="group flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3 transition-all duration-300 hover:-translate-y-0.5 hover:border-white/[0.14] hover:bg-white/[0.04]">
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-white/[0.07] bg-omnivra-surface-2/80 transition-transform duration-300 group-hover:scale-110">
        {mark}
      </span>
      <span className="min-w-0">
        <span className="block truncate text-sm font-semibold text-[#e4e4e7]">{name}</span>
        {sub && <span className="block truncate text-[11px] text-[#a1a1aa]">{sub}</span>}
      </span>
    </div>
  )
}
