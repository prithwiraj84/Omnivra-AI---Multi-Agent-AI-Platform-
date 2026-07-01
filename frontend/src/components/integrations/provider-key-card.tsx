/**
 * ProviderKeyCard — configure one provider's API key from the browser. Shows where the active
 * key comes from (environment vs a key you saved here), lets you paste/replace or remove a key,
 * and expands step-by-step docs + a "get a key" link. Raw keys are never shown back — only a
 * masked hint of a stored key. Saving/removing hits the backend, which uses the key immediately.
 */
import axios from 'axios'
import { useState } from 'react'
import {
  BookOpen,
  Check,
  ExternalLink,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  Trash2,
  type LucideIcon,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { GlassCard } from '@/components/ui/glass-card'
import { IconTile } from '@/components/ui/icon-tile'
import { NeonBadge } from '@/components/ui/neon-badge'
import { StatusDot } from '@/components/ui/status-dot'
import { useClearProviderKey, useSaveProviderKey } from '@/hooks/useSystem'
import type { ProviderKeyStatus } from '@/lib/api/system'
import type { Accent } from '@/types'

/** Static per-provider display metadata (icon/accent + how-to-get-a-key docs). */
export interface ProviderKeyMeta {
  id: string
  name: string
  icon: LucideIcon
  accent: Accent
  category: 'llm' | 'media'
  docUrl: string
  /** Short "how to get a key" steps shown in the disclosure. */
  steps: string[]
  /** Optional hint about what the key unlocks. */
  detail: string
}

/** Turn a save/clear failure into a friendly message (surfaces the backend 422 detail). */
function keyErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    if (detail) return detail
    if (!error.response) return 'Could not reach the server. Is the backend running?'
  }
  return 'Could not save the key. Please try again.'
}

export function ProviderKeyCard({ meta, status }: { meta: ProviderKeyMeta; status?: ProviderKeyStatus }) {
  const Icon = meta.icon
  const save = useSaveProviderKey()
  const clear = useClearProviderKey()
  const [value, setValue] = useState('')
  const [reveal, setReveal] = useState(false)
  const [showDocs, setShowDocs] = useState(false)
  const [saved, setSaved] = useState(false)

  const source = status?.source ?? 'none'
  const configured = status?.configured ?? false
  const busy = save.isPending || clear.isPending

  function onSave() {
    const trimmed = value.trim()
    if (!trimmed) return
    setSaved(false)
    save.mutate(
      { id: meta.id, value: trimmed },
      {
        onSuccess: () => {
          setValue('')
          setReveal(false)
          setSaved(true)
        },
      },
    )
  }

  function onClear() {
    setSaved(false)
    clear.mutate(meta.id)
  }

  return (
    <GlassCard padding="md" glow={configured ? meta.accent : undefined} className="flex flex-col gap-4">
      {/* header + current status */}
      <div className="flex items-start gap-3">
        <IconTile accent={meta.accent} icon={Icon} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <p className="truncate text-sm font-medium text-zinc-100">{meta.name}</p>
            <StatusDot status={configured ? 'online' : 'idle'} pulse={configured} label={configured ? 'Active' : 'Off'} />
          </div>
          <p className="truncate text-xs text-zinc-500">{meta.detail}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {source === 'stored' && (
          <>
            <NeonBadge tone="success" dot>
              Custom key
            </NeonBadge>
            {status?.masked && (
              <code className="rounded bg-white/[0.04] px-1.5 py-0.5 font-mono text-[11px] text-[#a1a1aa]">
                {status.masked}
              </code>
            )}
          </>
        )}
        {source === 'env' && (
          <NeonBadge tone="info" dot>
            From environment
          </NeonBadge>
        )}
        {source === 'none' && (
          <NeonBadge tone="warning" dot>
            Not configured
          </NeonBadge>
        )}
        <span className="ml-auto font-mono text-[10px] uppercase tracking-wide text-[#52525b]">{status?.envVar ?? meta.id}</span>
      </div>

      {/* enter / replace key */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <div className="relative flex flex-1 items-center">
            <KeyRound className="pointer-events-none absolute left-3 h-4 w-4 text-[#71717a]" aria-hidden />
            <input
              type={reveal ? 'text' : 'password'}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') onSave()
              }}
              placeholder={source === 'stored' ? 'Replace saved key…' : 'Paste your API key'}
              aria-label={`${meta.name} API key`}
              autoComplete="off"
              spellCheck={false}
              className="focus-ring h-10 w-full rounded-md bg-omnivra-surface-2 pl-9 pr-9 font-mono text-sm text-[#e4e4e7] placeholder:font-sans placeholder:text-[#71717a]"
            />
            <button
              type="button"
              onClick={() => setReveal((r) => !r)}
              aria-label={reveal ? 'Hide key' : 'Show key'}
              className="focus-ring absolute right-2 rounded p-1 text-[#71717a] hover:text-[#a1a1aa]"
            >
              {reveal ? <EyeOff className="h-4 w-4" aria-hidden /> : <Eye className="h-4 w-4" aria-hidden />}
            </button>
          </div>
          <Button size="sm" onClick={onSave} disabled={busy || !value.trim()}>
            {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : 'Save'}
          </Button>
        </div>

        {/* feedback */}
        {save.isError && (
          <p role="alert" aria-live="polite" className="text-xs text-omnivra-pink">
            {keyErrorMessage(save.error)}
          </p>
        )}
        {clear.isError && (
          <p role="alert" aria-live="polite" className="text-xs text-omnivra-pink">
            {keyErrorMessage(clear.error)}
          </p>
        )}
        {saved && !save.isError && (
          <p aria-live="polite" className="inline-flex items-center gap-1 text-xs text-omnivra-emerald-bright">
            <Check className="h-3.5 w-3.5" aria-hidden /> Saved — the backend is now using this key.
          </p>
        )}
      </div>

      {/* actions: docs toggle + remove */}
      <div className="flex items-center justify-between border-t border-white/[0.06] pt-3">
        <button
          type="button"
          onClick={() => setShowDocs((s) => !s)}
          aria-expanded={showDocs}
          className="focus-ring inline-flex items-center gap-1.5 rounded text-xs font-medium text-[#a1a1aa] transition-colors hover:text-white"
        >
          <BookOpen className="h-3.5 w-3.5" aria-hidden />
          {showDocs ? 'Hide guide' : 'How to get a key'}
        </button>
        {status?.storedSet && (
          <button
            type="button"
            onClick={onClear}
            disabled={busy}
            className="focus-ring inline-flex items-center gap-1.5 rounded text-xs font-medium text-omnivra-red/80 transition-colors hover:text-omnivra-red disabled:opacity-50"
          >
            {clear.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Trash2 className="h-3.5 w-3.5" aria-hidden />}
            Remove
          </button>
        )}
      </div>

      {showDocs && (
        <div className="flex flex-col gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          <ol className="flex list-decimal flex-col gap-1.5 pl-4 text-xs leading-relaxed text-[#a1a1aa]">
            {meta.steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
          <a
            href={meta.docUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="focus-ring inline-flex w-fit items-center gap-1.5 rounded text-xs font-semibold text-omnivra-cyan hover:text-white"
          >
            Open {meta.name} keys
            <ExternalLink className="h-3.5 w-3.5" aria-hidden />
          </a>
        </div>
      )}
    </GlassCard>
  )
}
