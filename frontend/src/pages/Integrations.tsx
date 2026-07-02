import type { LucideIcon } from 'lucide-react'
import { Clapperboard, Cpu, Database, Facebook, Instagram, KeyRound, Linkedin, Plug, Send, ShieldCheck, Sparkles, Youtube, Zap } from 'lucide-react'

import { ProviderKeyCard, type ProviderKeyMeta } from '@/components/integrations/provider-key-card'
import { SocialConnectorCard, type SocialConnectorMeta } from '@/components/integrations/social-connector-card'
import { FacebookMark, InstagramMark, LinkedInMark, XMark, YouTubeMark } from '@/components/landing/brand-marks'
import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { StatusDot } from '@/components/ui/status-dot'
import { IconTile } from '@/components/ui/icon-tile'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { useProviderKeys, useSocialConnectors, useSystemInfo } from '@/hooks/useSystem'
import type { Accent } from '@/types'

/** A status tile descriptor for the read-only platform-service cards. */
interface StatusTile {
  key: string
  name: string
  detail: string
  icon: LucideIcon
  accent: Accent
  configured: boolean
  offLabel?: string
  offTone?: BadgeTone
  offDot?: string
}

/**
 * Configurable provider keys (LLM + media). `steps` is the "how to get a key" guide shown in
 * each card's disclosure; the id must match the backend catalog (services/provider_keys.py).
 */
const KEY_PROVIDERS: ProviderKeyMeta[] = [
  {
    id: 'google_ai',
    name: 'Google AI Studio',
    icon: Sparkles,
    accent: 'cyan',
    category: 'llm',
    detail: 'Gemini models — used by the CEO and several agents',
    docUrl: 'https://aistudio.google.com/app/apikey',
    steps: [
      'Sign in at aistudio.google.com with a Google account.',
      'Open “Get API key” → “Create API key”.',
      'Copy the key (starts with AIza…) and paste it here.',
    ],
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    icon: Cpu,
    accent: 'violet',
    category: 'llm',
    detail: 'Routes most engineering, marketing & docs agents',
    docUrl: 'https://openrouter.ai/keys',
    steps: [
      'Create an account at openrouter.ai.',
      'Go to Keys → “Create key”.',
      'Copy the key (sk-or-…) and paste it here.',
      'Add credits, or pick free models to start.',
    ],
  },
  {
    id: 'groq',
    name: 'Groq',
    icon: Zap,
    accent: 'amber',
    category: 'llm',
    detail: 'Ultra-fast inference + Orpheus / PlayAI voice',
    docUrl: 'https://console.groq.com/keys',
    steps: [
      'Sign up at console.groq.com.',
      'Open “API Keys” → “Create API Key”.',
      'Copy the key (gsk_…) and paste it here.',
    ],
  },
  {
    id: 'huggingface',
    name: 'Hugging Face',
    icon: Plug,
    accent: 'blue',
    category: 'llm',
    detail: 'FLUX image generation + speech-to-text',
    docUrl: 'https://huggingface.co/settings/tokens',
    steps: [
      'Sign in at huggingface.co.',
      'Open Settings → Access Tokens → “New token” (Read).',
      'Copy the token (hf_…) and paste it here.',
    ],
  },
  {
    id: 'pexels',
    name: 'Pexels',
    icon: Clapperboard,
    accent: 'emerald',
    category: 'media',
    detail: 'Stock b-roll for rendered reels (optional)',
    docUrl: 'https://www.pexels.com/api/new/',
    steps: [
      'Create a free account at pexels.com.',
      'Open the API page and request a key.',
      'Copy the key and paste it here.',
    ],
  },
]

/** Per-connector display metadata (brand mark + header icon + accent), keyed by connector id. */
const SOCIAL_META: Record<string, { meta: SocialConnectorMeta; icon: LucideIcon }> = {
  youtube: { meta: { id: 'youtube', mark: <YouTubeMark className="h-5 w-5" />, accent: 'pink' }, icon: Youtube },
  linkedin: { meta: { id: 'linkedin', mark: <LinkedInMark className="h-5 w-5" />, accent: 'blue' }, icon: Linkedin },
  facebook: { meta: { id: 'facebook', mark: <FacebookMark className="h-5 w-5" />, accent: 'blue' }, icon: Facebook },
  instagram: { meta: { id: 'instagram', mark: <InstagramMark className="h-5 w-5" />, accent: 'pink' }, icon: Instagram },
  twitter: { meta: { id: 'twitter', mark: <XMark className="h-5 w-5 text-white" />, accent: 'violet' }, icon: Send },
}

/** One read-only integration card: tile + name, a presence dot and a Configured badge. */
function StatusCard({ tile }: { tile: StatusTile }) {
  const Icon = tile.icon
  return (
    <GlassCard interactive glow={tile.configured ? tile.accent : undefined} padding="md" className="flex flex-col gap-4">
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
 * Integrations — connect the AI providers. LLM + media provider keys are now editable IN THE
 * BROWSER (GET/PUT/DELETE /system/provider-keys): a key you save is stored on the server and used
 * on the very next call; env-configured keys are shown as read-only "From environment". Platform
 * services (Supabase, Auth) remain read-only status. Offline (jsdom/tests) the cards render from
 * the static catalog as "Not configured" without crashing.
 */
export function Integrations() {
  const { data: keys } = useProviderKeys()
  const { data: info } = useSystemInfo()
  const { data: connectors } = useSocialConnectors()

  const byId = new Map((keys ?? []).map((k) => [k.id, k]))
  const llm = KEY_PROVIDERS.filter((p) => p.category === 'llm')
  const media = KEY_PROVIDERS.filter((p) => p.category === 'media')

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
            <p className="text-sm font-medium text-zinc-100">Configure your provider keys</p>
            <p className="max-w-prose text-xs leading-relaxed text-[#71717a]">
              Paste a key below to connect a provider right from here — it’s stored on the server and used
              immediately, no restart needed. Keys already set in{' '}
              <span className="font-mono text-[#a1a1aa]">backend/.env</span> show as{' '}
              <span className="text-[#a1a1aa]">From environment</span>; a key you save here overrides it.
              Keys are never shown back in full.
            </p>
          </div>
        </GlassCard>
      </Reveal>

      <section className="flex flex-col gap-3">
        <SectionHeader label="LLM Providers" count={llm.length} />
        <Stagger className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {llm.map((meta) => (
            <StaggerItem key={meta.id}>
              <ProviderKeyCard meta={meta} status={byId.get(meta.id)} />
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      <section className="flex flex-col gap-3">
        <SectionHeader label="Media Providers" count={media.length} />
        <Stagger className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {media.map((meta) => (
            <StaggerItem key={meta.id}>
              <ProviderKeyCard meta={meta} status={byId.get(meta.id)} />
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      {connectors && connectors.length > 0 && (
        <section className="flex flex-col gap-3">
          <SectionHeader label="Publishing & Social" count={connectors.length} />
          <p className="-mt-1 max-w-prose text-xs leading-relaxed text-[#a1a1aa]">
            Add each platform’s API credentials to publish reels and posts. Tokens are stored on the server,
            masked here, and never committed. YouTube uploads for real today; the others save now and go live
            as each platform’s publishing is wired in.
          </p>
          <Stagger className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {connectors.map((c) => {
              const m = SOCIAL_META[c.id]
              if (!m) return null
              return (
                <StaggerItem key={c.id}>
                  <SocialConnectorCard connector={c} meta={m.meta} icon={m.icon} />
                </StaggerItem>
              )
            })}
          </Stagger>
        </section>
      )}

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
