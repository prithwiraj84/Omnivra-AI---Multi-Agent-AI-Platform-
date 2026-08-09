/**
 * Error Log (cp-0071) — every failure the app hit, in one place the user can actually read.
 *
 * The backend captures WARNING+ from its logging funnel (provider/LLM failures, API & LLM
 * rate limits, voice/media misses, render errors, auth/key problems, network faults, unhandled
 * crashes), classifies them into user-meaningful categories and coalesces repeats (×N).
 * This page adds the reading tools: category chips with live counts, an errors/warnings level
 * filter, free-text search, expandable per-row detail, relative timestamps, and Clear.
 * Live: the 'error_log' WebSocket frame refreshes the list the moment something fails.
 */
import { useEffect, useMemo, useState } from 'react'
import {
  Check,
  ChevronDown,
  Copy,
  Clock3,
  Database,
  FileWarning,
  Film,
  Gauge,
  KeyRound,
  Loader2,
  Megaphone,
  Mic,
  Search,
  ShieldCheck,
  Cpu,
  Trash2,
  TriangleAlert,
  Wifi,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Reveal } from '@/components/common/reveal'
import { cn } from '@/lib/utils'
import { useClearErrorLog, useErrorLog } from '@/hooks/useErrorLog'
import { useUIStore } from '@/store/ui'
import type { ErrorItem } from '@/lib/api/errorLog'

/** Category id -> presentation. Mirrors services/error_log.py CATEGORIES. */
const CATEGORY_VIEW: Record<string, { label: string; icon: LucideIcon; tone: BadgeTone }> = {
  rate_limit: { label: 'Rate limit', icon: Gauge, tone: 'warning' },
  llm: { label: 'LLM / Agents', icon: Cpu, tone: 'violet' },
  media: { label: 'Media / Voice', icon: Mic, tone: 'info' },
  render: { label: 'Render / Apps', icon: Film, tone: 'info' },
  publish: { label: 'Social / Publish', icon: Megaphone, tone: 'info' },
  documents: { label: 'Documents', icon: FileWarning, tone: 'info' },
  auth: { label: 'Auth / Keys', icon: KeyRound, tone: 'danger' },
  database: { label: 'Database', icon: Database, tone: 'info' },
  network: { label: 'Network', icon: Wifi, tone: 'warning' },
  system: { label: 'System', icon: TriangleAlert, tone: 'cyan' },
}

/** One error as pasteable text — what a bug report or a support message actually needs. */
export function formatErrorForCopy(item: ErrorItem): string {
  const lines = [
    `[${item.level.toUpperCase()}] ${CATEGORY_VIEW[item.category]?.label ?? item.category}${item.count > 1 ? ` (x${item.count})` : ''}`,
    item.message,
    `source: ${item.source}`,
    `time: ${item.lastTs}`,
  ]
  if (item.detail) lines.push(`detail: ${item.detail}`)
  return lines.join('\n')
}

/** Copy text to the clipboard; resolves false where the API is unavailable (http, jsdom). */
async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

/** Compact "how long ago" for a log row. */
function timeAgo(iso: string): string {
  const ms = Date.now() - Date.parse(iso)
  if (Number.isNaN(ms) || ms < 0) return 'now'
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

function ErrorRow({ item }: { item: ErrorItem }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const view = CATEGORY_VIEW[item.category] ?? CATEGORY_VIEW.system
  const expandable = Boolean(item.detail) || item.message.length > 160

  const onCopy = async (e: React.MouseEvent) => {
    e.stopPropagation() // the row toggles detail on click — copying must not also toggle
    if (await copyText(formatErrorForCopy(item))) {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }
  }
  return (
    <div
      className={cn(
        'rounded-lg border bg-white/[0.02] transition-colors duration-200',
        item.level === 'error' ? 'border-omnivra-red/20' : 'border-white/[0.06]',
      )}
    >
      <button
        type="button"
        onClick={() => expandable && setOpen((o) => !o)}
        aria-expanded={expandable ? open : undefined}
        className={cn(
          'focus-ring flex w-full items-start gap-3 px-3 py-2.5 text-left',
          expandable && 'cursor-pointer',
        )}
      >
        <NeonBadge tone={item.level === 'error' ? 'danger' : 'warning'} dot className="mt-0.5 shrink-0">
          {item.level}
        </NeonBadge>
        <NeonBadge tone={view.tone} className="mt-0.5 hidden shrink-0 sm:inline-flex">
          {view.label}
        </NeonBadge>
        <div className="min-w-0 flex-1">
          <p className={cn('text-xs leading-relaxed text-[#e4e4e7]', !open && 'line-clamp-2')}>{item.message}</p>
          <p className="mt-0.5 truncate font-mono text-[10px] text-[#52525b]">{item.source}</p>
        </div>
        <span className="mt-0.5 flex shrink-0 items-center gap-2 text-[11px] text-[#71717a]">
          <span
            role="button"
            tabIndex={0}
            aria-label="Copy this error"
            title="Copy this error"
            onClick={onCopy}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') void onCopy(e as unknown as React.MouseEvent)
            }}
            className="focus-ring rounded p-0.5 transition-colors duration-200 hover:text-omnivra-cyan"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-omnivra-emerald" aria-hidden /> : <Copy className="h-3.5 w-3.5" aria-hidden />}
          </span>
          {item.count > 1 && (
            <span className="tabular rounded bg-white/[0.06] px-1.5 font-semibold text-omnivra-amber">
              ×{item.count}
            </span>
          )}
          <span className="tabular inline-flex items-center gap-1">
            <Clock3 className="h-3 w-3" aria-hidden />
            {timeAgo(item.lastTs)}
          </span>
          {expandable && (
            <ChevronDown className={cn('h-3.5 w-3.5 transition-transform duration-200', open && 'rotate-180')} aria-hidden />
          )}
        </span>
      </button>
      {open && item.detail && (
        <pre className="overflow-x-auto whitespace-pre-wrap break-words border-t border-white/[0.06] px-3 py-2 font-mono text-[11px] leading-relaxed text-[#a1a1aa]">
          {item.detail}
        </pre>
      )}
    </div>
  )
}

export function ErrorLog() {
  const { data, isLoading } = useErrorLog()
  const clear = useClearErrorLog()
  const markErrorsSeen = useUIStore((s) => s.markErrorsSeen)
  const [category, setCategory] = useState<string | null>(null)
  const [level, setLevel] = useState<'all' | 'error' | 'warning'>('all')
  const [query, setQuery] = useState('')
  const [copiedAll, setCopiedAll] = useState(false)

  // Opening the page is what "reads" the log: the sidebar badge counts records newer than this.
  // Re-marked whenever new data arrives while the page is open, so the badge never lags behind
  // what the user is literally looking at.
  useEffect(() => {
    markErrorsSeen()
  }, [data, markErrorsSeen])

  const items = data?.items ?? []
  const counts = data?.counts ?? {}
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return items.filter(
      (e) =>
        (!category || e.category === category) &&
        (level === 'all' || e.level === level) &&
        (!q || e.message.toLowerCase().includes(q) || e.source.toLowerCase().includes(q)),
    )
  }, [items, category, level, query])

  const errorTotal = items.filter((e) => e.level === 'error').length
  // Only categories that actually occurred get a chip — a fixed list would be mostly dead UI.
  const activeCategories = Object.keys(CATEGORY_VIEW).filter((c) => (counts[c] ?? 0) > 0)

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <GlassCard padding="md" className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <SectionHeader label="Error Log" count={data?.total ?? 0} />
            <span className="text-[11px] text-[#71717a]" aria-live="polite">
              {errorTotal > 0 ? `${errorTotal} error${errorTotal === 1 ? '' : 's'} · live` : 'live'}
            </span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={filtered.length === 0}
              onClick={async () => {
                // Copies what the user SEES — the active category/level/search filters apply.
                if (await copyText(filtered.map(formatErrorForCopy).join('\n\n'))) {
                  setCopiedAll(true)
                  setTimeout(() => setCopiedAll(false), 1500)
                }
              }}
              className="ml-auto"
            >
              {copiedAll ? <Check className="h-3.5 w-3.5 text-omnivra-emerald" aria-hidden /> : <Copy className="h-3.5 w-3.5" aria-hidden />}
              {copiedAll ? 'Copied' : 'Copy log'}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={clear.isPending || items.length === 0}
              onClick={() => clear.mutate()}
              className="hover:text-omnivra-red"
            >
              {clear.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Trash2 className="h-3.5 w-3.5" aria-hidden />}
              Clear
            </Button>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Level filter */}
            <div className="inline-flex rounded-md bg-omnivra-surface-2 p-0.5" role="group" aria-label="Level filter">
              {(['all', 'error', 'warning'] as const).map((l) => (
                <button
                  key={l}
                  type="button"
                  aria-pressed={level === l}
                  onClick={() => setLevel(l)}
                  className={cn(
                    'focus-ring rounded px-2.5 py-1 text-[11px] font-medium capitalize transition-colors duration-200',
                    level === l ? 'bg-omnivra-surface-3 text-omnivra-cyan' : 'text-[#a1a1aa] hover:text-[#e4e4e7]',
                  )}
                >
                  {l === 'all' ? 'All' : `${l}s`}
                </button>
              ))}
            </div>

            {/* Category chips with live counts */}
            {activeCategories.map((c) => {
              const view = CATEGORY_VIEW[c]
              const on = category === c
              return (
                <button
                  key={c}
                  type="button"
                  aria-pressed={on}
                  onClick={() => setCategory(on ? null : c)}
                  className={cn(
                    'focus-ring inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors duration-200',
                    on
                      ? 'border-omnivra-cyan/40 bg-omnivra-cyan/10 text-omnivra-cyan'
                      : 'border-white/10 text-[#71717a] hover:text-[#a1a1aa]',
                  )}
                >
                  <view.icon className="h-3 w-3" aria-hidden />
                  {view.label}
                  <span className="tabular">{counts[c]}</span>
                </button>
              )
            })}

            {/* Search */}
            <div className="relative ml-auto min-w-[12rem] flex-1 sm:max-w-xs">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#71717a]" aria-hidden />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search message or source…"
                aria-label="Search errors"
                className="focus-ring w-full rounded-md bg-omnivra-surface-2 py-1.5 pl-8 pr-3 text-xs text-[#e4e4e7] placeholder:text-[#71717a]"
              />
            </div>
          </div>
        </GlassCard>
      </Reveal>

      {filtered.length === 0 ? (
        <EmptyState
          icon={items.length === 0 ? ShieldCheck : Search}
          title={items.length === 0 ? (isLoading ? 'Loading…' : 'No errors recorded') : 'Nothing matches the filters'}
          hint={
            items.length === 0
              ? 'Provider failures, rate limits, voice/render misses and system errors will appear here the moment they happen.'
              : 'Try clearing the category, level or search filters.'
          }
          className="py-16"
        />
      ) : (
        <div className="flex flex-col gap-2">
          {filtered.map((item) => (
            <ErrorRow key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}
