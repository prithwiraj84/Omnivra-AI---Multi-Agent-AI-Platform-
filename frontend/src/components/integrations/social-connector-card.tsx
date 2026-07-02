/**
 * SocialConnectorCard — configure one social platform's publishing credentials from the browser.
 * Renders the platform's brand mark, its content kinds, a connection badge, an optional caveat
 * note, and a multi-field credential form (secret fields are masked + reveal-toggle). Saving
 * writes every touched field in one request; raw values are never shown back (only a masked hint
 * of what's stored). When real publishing isn't wired yet, the card says so honestly.
 */
import axios from 'axios'
import { useState } from 'react'
import { BookOpen, Check, ExternalLink, Eye, EyeOff, Info, Loader2, Trash2, type LucideIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { GlassCard } from '@/components/ui/glass-card'
import { NeonBadge } from '@/components/ui/neon-badge'
import { useClearSocialConnector, useSaveSocialConnector } from '@/hooks/useSystem'
import type { SocialConnector } from '@/lib/api/system'
import type { Accent } from '@/types'
import { cn } from '@/lib/utils'

export interface SocialConnectorMeta {
  id: string
  mark: React.ReactNode
  accent: Accent
}

const ACCENT_TILE: Record<string, string> = {
  cyan: 'border-omnivra-cyan/30',
  blue: 'border-omnivra-blue/30',
  violet: 'border-omnivra-violet/30',
  emerald: 'border-omnivra-emerald-bright/30',
  amber: 'border-omnivra-amber/30',
  pink: 'border-omnivra-pink/30',
}

function connErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    if (detail) return detail
    if (!error.response) return 'Could not reach the server. Is the backend running?'
  }
  return 'Could not save. Please try again.'
}

export function SocialConnectorCard({
  connector,
  meta,
  icon: Icon,
}: {
  connector: SocialConnector
  meta: SocialConnectorMeta
  icon: LucideIcon
}) {
  const save = useSaveSocialConnector()
  const clear = useClearSocialConnector()
  const [draft, setDraft] = useState<Record<string, string>>({})
  const [reveal, setReveal] = useState(false)
  const [saved, setSaved] = useState(false)

  const busy = save.isPending || clear.isPending
  const anyStored = connector.fields.some((f) => f.storedSet)
  const touched = Object.keys(draft).length > 0

  function onSave() {
    if (!touched) return
    setSaved(false)
    save.mutate(
      { id: connector.id, values: draft },
      {
        onSuccess: () => {
          setDraft({})
          setReveal(false)
          setSaved(true)
        },
      },
    )
  }

  function onDisconnect() {
    setSaved(false)
    setDraft({})
    clear.mutate(connector.id)
  }

  return (
    <GlassCard padding="md" glow={connector.configured ? meta.accent : undefined} className="flex flex-col gap-4">
      {/* header */}
      <div className="flex items-start gap-3">
        <span className={cn('grid h-10 w-10 shrink-0 place-items-center rounded-xl border bg-omnivra-surface-2/80', ACCENT_TILE[meta.accent])}>
          {meta.mark}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Icon className="h-4 w-4 text-[#a1a1aa]" aria-hidden />
            <p className="truncate text-sm font-semibold text-white">{connector.label}</p>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-1.5">
            {connector.kinds.map((k) => (
              <span key={k} className="rounded-full bg-white/[0.05] px-1.5 py-0.5 text-[10px] font-medium capitalize text-[#a1a1aa]">
                {k}
              </span>
            ))}
          </div>
        </div>
        {connector.configured ? (
          <NeonBadge tone={connector.publishSupported ? 'success' : 'warning'} dot>
            {connector.publishSupported ? 'Ready' : 'Saved'}
          </NeonBadge>
        ) : (
          <NeonBadge tone="info" dot>
            Not connected
          </NeonBadge>
        )}
      </div>

      {/* publish-status note */}
      {!connector.publishSupported && (
        <p className="inline-flex items-start gap-1.5 rounded-lg border border-omnivra-amber/20 bg-omnivra-amber/[0.06] px-2.5 py-1.5 text-[11px] leading-relaxed text-omnivra-amber">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
          Save your credentials now — real publishing to {connector.label} lands in an upcoming update.
        </p>
      )}
      {connector.note && (
        <p className="text-[11px] leading-relaxed text-[#a1a1aa]">{connector.note}</p>
      )}

      {/* credential fields */}
      <div className="flex flex-col gap-2.5">
        {connector.fields.map((f) => {
          const value = draft[f.key] ?? ''
          const placeholder =
            f.source === 'stored'
              ? `Saved${f.masked ? ` · ${f.masked}` : ''} — type to replace`
              : f.source === 'env'
                ? 'Set from environment — type to override'
                : f.placeholder || `Enter ${f.label.toLowerCase()}`
          return (
            <label key={f.key} className="flex flex-col gap-1">
              <span className="flex items-center justify-between text-[11px] font-medium text-[#d4d4d8]">
                <span>
                  {f.label}
                  {f.required && <span className="ml-1 text-omnivra-pink/70">*</span>}
                </span>
                {f.source !== 'none' && (
                  <span className="text-[10px] font-normal text-[#a1a1aa]">
                    {f.source === 'stored' ? 'Custom' : 'From env'}
                  </span>
                )}
              </span>
              <div className="relative flex items-center">
                <input
                  type={f.secret && !reveal ? 'password' : 'text'}
                  value={value}
                  onChange={(e) => setDraft((d) => ({ ...d, [f.key]: e.target.value }))}
                  placeholder={placeholder}
                  aria-label={`${connector.label} ${f.label}`}
                  autoComplete="off"
                  spellCheck={false}
                  className="focus-ring h-9 w-full rounded-md bg-omnivra-surface-2 px-3 font-mono text-xs text-[#e4e4e7] placeholder:font-sans placeholder:text-[#71717a]"
                />
              </div>
            </label>
          )
        })}
      </div>

      {/* feedback */}
      {save.isError && (
        <p role="alert" aria-live="polite" className="text-xs text-omnivra-pink">
          {connErrorMessage(save.error)}
        </p>
      )}
      {clear.isError && (
        <p role="alert" aria-live="polite" className="text-xs text-omnivra-pink">
          {connErrorMessage(clear.error)}
        </p>
      )}
      {saved && !save.isError && (
        <p aria-live="polite" className="inline-flex items-center gap-1 text-xs text-omnivra-emerald-bright">
          <Check className="h-3.5 w-3.5" aria-hidden /> Saved.
        </p>
      )}

      {/* actions */}
      <div className="flex items-center gap-2 border-t border-white/[0.06] pt-3">
        <Button size="sm" onClick={onSave} disabled={busy || !touched}>
          {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : 'Save'}
        </Button>
        {connector.fields.some((f) => f.secret) && (
          <button
            type="button"
            onClick={() => setReveal((r) => !r)}
            aria-label={reveal ? 'Hide secrets' : 'Show secrets'}
            className="focus-ring inline-flex items-center gap-1 rounded p-1.5 text-[#a1a1aa] hover:text-white"
          >
            {reveal ? <EyeOff className="h-4 w-4" aria-hidden /> : <Eye className="h-4 w-4" aria-hidden />}
          </button>
        )}
        <a
          href={connector.docUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="focus-ring ml-auto inline-flex items-center gap-1.5 rounded text-xs font-medium text-[#a1a1aa] transition-colors hover:text-white"
        >
          <BookOpen className="h-3.5 w-3.5" aria-hidden />
          Get tokens
          <ExternalLink className="h-3 w-3" aria-hidden />
        </a>
        {anyStored && (
          <button
            type="button"
            onClick={onDisconnect}
            disabled={busy}
            aria-label={`Disconnect ${connector.label}`}
            className="focus-ring inline-flex items-center gap-1 rounded text-xs font-medium text-omnivra-red/80 transition-colors hover:text-omnivra-red disabled:opacity-50"
          >
            {clear.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Trash2 className="h-3.5 w-3.5" aria-hidden />}
          </button>
        )}
      </div>
    </GlassCard>
  )
}
