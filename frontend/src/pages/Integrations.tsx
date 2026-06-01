import type { LucideIcon } from 'lucide-react'
import { Cpu, Database, KeyRound, Plug, ShieldCheck, Sparkles, Zap } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { StatusDot } from '@/components/ui/status-dot'
import { IconTile } from '@/components/ui/icon-tile'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { useProviders, useSystemInfo } from '@/hooks/useSystem'
import type { Accent, ProviderKey } from '@/types'

/** A status tile descriptor: an LLM provider or a platform service. */
interface StatusTile {
  key: string
  name: string
  detail: string
  icon: LucideIcon
  accent: Accent
  configured: boolean
  // Optional copy for the NOT-configured state. Defaults to the neutral
  // "Idle / Not configured"; used to present an intentional state (e.g. auth open
  // mode) as valid rather than broken.
  offLabel?: string
  offTone?: BadgeTone
  offDot?: string
}

/** Provider display metadata (order + icon + accent), keyed by ProviderKey. */
const PROVIDER_META: { key: ProviderKey; name: string; icon: LucideIcon; accent: Accent }[] = [
  { key: 'google_ai', name: 'Google AI Studio', icon: Sparkles, accent: 'cyan' },
  { key: 'openrouter', name: 'OpenRouter', icon: Cpu, accent: 'violet' },
  { key: 'groq', name: 'Groq', icon: Zap, accent: 'amber' },
  { key: 'huggingface', name: 'Hugging Face', icon: Plug, accent: 'blue' },
]

/** One integration card: tile + name, a presence dot and a Configured / Not configured badge. */
function StatusCard({ tile }: { tile: StatusTile }) {
  const Icon = tile.icon
  return (
    <GlassCard
      interactive
      glow={tile.configured ? tile.accent : undefined}
      padding="md"
      className="flex flex-col gap-4"
    >
      <div className="flex items-start gap-3">
        <IconTile accent={tile.accent} icon={Icon} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-zinc-100">{tile.name}</p>
          <p className="truncate text-xs text-zinc-500">{tile.detail}</p>
        </div>
      </div>
      <div className="flex items-center justify-between border-t border-white/[0.06] pt-3">
        <StatusDot
          status={tile.configured ? 'online' : 'idle'}
          pulse={tile.configured}
          label={tile.configured ? 'Online' : (tile.offDot ?? 'Idle')}
        />
        <NeonBadge tone={tile.configured ? 'success' : (tile.offTone ?? 'info')} dot>
          {tile.configured ? 'Configured' : (tile.offLabel ?? 'Not configured')}
        </NeonBadge>
      </div>
    </GlassCard>
  )
}

/**
 * Integrations — the connected-services view. Renders one card per LLM provider
 * (Google AI Studio, OpenRouter, Groq, Hugging Face) using the live
 * GET /system/providers flags, plus platform-service cards for Supabase
 * (supabaseConfigured) and Auth (authEnabled) from GET /system/info. Each card
 * shows a presence StatusDot and a "Configured / Not configured" NeonBadge.
 * Read-only; a hint reminds operators that keys live in backend/.env. Offline
 * (jsdom/tests) everything resolves to "Not configured" without crashing.
 */
export function Integrations() {
  const { data: providers } = useProviders()
  const { data: info } = useSystemInfo()

  const providerTiles: StatusTile[] = PROVIDER_META.map((meta) => ({
    key: meta.key,
    name: meta.name,
    detail: 'LLM provider',
    icon: meta.icon,
    accent: meta.accent,
    configured: providers?.[meta.key] ?? false,
  }))

  const platformTiles: StatusTile[] = [
    {
      key: 'supabase',
      name: 'Supabase',
      detail: 'Database & vector store',
      icon: Database,
      accent: 'emerald',
      configured: info?.supabaseConfigured ?? false,
    },
    {
      key: 'auth',
      name: 'Authentication',
      detail: 'JWT bearer auth gate (open in dev)',
      icon: ShieldCheck,
      accent: 'violet',
      configured: info?.authEnabled ?? false,
      // Open mode is the intentional dev default — show it as a valid state, not "broken".
      offLabel: 'Open (dev mode)',
      offTone: 'warning',
      offDot: 'Open',
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <Reveal>
        <GlassCard padding="md" className="flex items-start gap-3">
          <IconTile accent="cyan" icon={KeyRound} />
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-zinc-100">API keys live in the backend</p>
            <p className="max-w-prose text-xs leading-relaxed text-[#71717a]">
              Configure provider keys and the Supabase connection in{' '}
              <span className="font-mono text-[#a1a1aa]">backend/.env</span>, then restart the
              backend. This page reflects what the running server has loaded.
            </p>
          </div>
        </GlassCard>
      </Reveal>

      <section className="flex flex-col gap-3">
        <SectionHeader label="LLM Providers" count={providerTiles.length} />
        <Stagger className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {providerTiles.map((tile) => (
            <StaggerItem key={tile.key}>
              <StatusCard tile={tile} />
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      <section className="flex flex-col gap-3">
        <SectionHeader label="Platform Services" count={platformTiles.length} />
        <Stagger className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {platformTiles.map((tile) => (
            <StaggerItem key={tile.key}>
              <StatusCard tile={tile} />
            </StaggerItem>
          ))}
        </Stagger>
      </section>
    </div>
  )
}
