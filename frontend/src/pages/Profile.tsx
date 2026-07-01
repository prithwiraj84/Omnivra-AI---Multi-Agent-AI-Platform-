/**
 * Profile — the signed-in user's identity, built on the Supabase session (cp-0059). A glowing
 * animated hero (avatar with a rotating conic ring, name you can rename inline, provider chip),
 * then staggered cards: account details, sign-in method, quick actions, and session/sign-out.
 * Gracefully handles the signed-out / open-mode case (local admin, optional social sign-in).
 * All motion is reduced-motion aware (Reveal/Stagger + the global MotionConfig).
 */
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'
import {
  BadgeCheck,
  Check,
  Copy,
  Github,
  KeyRound,
  LogOut,
  Mail,
  Pencil,
  ShieldCheck,
  Sparkles,
  UserRound,
  X,
  type LucideIcon,
} from 'lucide-react'

import { GoogleMark, OAuthButtons } from '@/components/auth/oauth-buttons'
import { Reveal, Stagger, StaggerItem } from '@/components/common/reveal'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { GlassCard } from '@/components/ui/glass-card'
import { NeonBadge } from '@/components/ui/neon-badge'
import { SectionHeader } from '@/components/ui/section-header'
import { StatusDot } from '@/components/ui/status-dot'
import { useSupabaseAuth } from '@/hooks/useSupabaseAuth'
import {
  avatarUrl,
  displayName,
  formatDate,
  initials,
  providerLabel,
  providerOf,
} from '@/lib/user-profile'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/auth'

/** Small icon for the sign-in provider. */
function ProviderIcon({ provider, className }: { provider: string; className?: string }) {
  if (provider === 'google') return <GoogleMark />
  if (provider === 'github') return <Github className={cn('h-[18px] w-[18px]', className)} aria-hidden />
  return <Mail className={cn('h-[18px] w-[18px]', className)} aria-hidden />
}

/** A labelled row inside a detail card. */
function InfoRow({
  icon: Icon,
  label,
  children,
}: {
  icon: LucideIcon
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-3 py-2.5">
      <span className="inline-flex items-center gap-2 text-xs text-[#a1a1aa]">
        <Icon className="h-4 w-4 text-[#71717a]" aria-hidden />
        {label}
      </span>
      <span className="min-w-0 truncate text-right text-sm text-[#e4e4e7]">{children}</span>
    </div>
  )
}

export function Profile() {
  const navigate = useNavigate()
  const reduce = useReducedMotion() ?? false
  const { user, isAuthenticated, isConfigured, signOut, updateDisplayName } = useSupabaseAuth()
  const clearAuth = useAuthStore((s) => s.clearAuth)

  const name = isAuthenticated ? displayName(user) : 'Local Admin'
  const email = user?.email ?? null
  const photo = avatarUrl(user)
  const provider = providerOf(user)
  const verified = Boolean(user?.email_confirmed_at ?? user?.confirmed_at)

  // inline rename
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [saving, setSaving] = useState(false)
  const [nameErr, setNameErr] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const editBtnRef = useRef<HTMLButtonElement>(null)
  const wasEditing = useRef(false)

  // Return focus to the Edit trigger after leaving edit mode (its input/buttons unmount, which
  // would otherwise drop focus to <body> — WCAG 2.4.3).
  useEffect(() => {
    if (wasEditing.current && !editing) editBtnRef.current?.focus()
    wasEditing.current = editing
  }, [editing])

  function beginEdit() {
    setDraft(name)
    setNameErr(null)
    setEditing(true)
  }

  async function saveName() {
    if (saving) return // guard: an Enter-mash must not fire concurrent updateUser calls
    const value = draft.trim()
    if (!value || value === name) {
      setEditing(false)
      return
    }
    setSaving(true)
    setNameErr(null)
    try {
      await updateDisplayName(value)
      setEditing(false)
    } catch {
      setNameErr('Could not update your name. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  async function copyId() {
    if (!user?.id) return
    try {
      await navigator.clipboard.writeText(user.id)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable — ignore */
    }
  }

  async function handleSignOut() {
    await signOut()
    clearAuth()
    navigate('/', { replace: true })
  }

  return (
    <div className="relative mx-auto flex w-full max-w-4xl flex-col gap-6">
      {/* ambient glow behind the hero */}
      <div aria-hidden className="pointer-events-none absolute inset-x-0 -top-8 h-56 bg-glow-cyan opacity-60 blur-2xl" />

      {/* ============ HERO ============ */}
      <Reveal className="relative">
        <GlassCard variant="strong" padding="lg" className="relative overflow-hidden">
          {/* decorative gradient banner */}
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-0 -top-16 h-40 bg-gradient-to-b from-omnivra-cyan/10 via-omnivra-purple/5 to-transparent"
          />

          <div className="relative flex flex-col items-center gap-5 text-center sm:flex-row sm:items-center sm:gap-6 sm:text-left">
            {/* avatar with rotating conic ring */}
            <div className="relative grid h-24 w-24 shrink-0 place-items-center">
              <motion.div
                aria-hidden
                className="absolute inset-0 rounded-full"
                style={{ background: 'conic-gradient(from 0deg, #22d3ee, #8b5cf6, #22d3ee)' }}
                animate={reduce ? undefined : { rotate: 360 }}
                transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
              />
              <div className="absolute inset-[3px] rounded-full bg-omnivra-surface-2" />
              <Avatar className="relative h-[86px] w-[86px] ring-0">
                {photo && <AvatarImage src={photo} alt={name} />}
                <AvatarFallback className="bg-omnivra-surface-3 text-xl font-semibold text-omnivra-cyan">
                  {isAuthenticated ? initials(name) : 'OM'}
                </AvatarFallback>
              </Avatar>
            </div>

            {/* identity */}
            <div className="flex min-w-0 flex-1 flex-col items-center gap-2 sm:items-start">
              {editing ? (
                <div className="flex w-full max-w-sm items-center gap-2">
                  <input
                    autoFocus
                    value={draft}
                    disabled={saving}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') saveName()
                      if (e.key === 'Escape') setEditing(false)
                    }}
                    aria-label="Display name"
                    className="focus-ring h-9 w-full rounded-md bg-omnivra-surface-2 px-3 text-lg font-semibold text-white disabled:opacity-60"
                  />
                  <Button size="sm" onClick={saveName} disabled={saving} aria-label="Save name">
                    {saving ? '…' : <Check className="h-4 w-4" aria-hidden />}
                  </Button>
                  <button
                    type="button"
                    onClick={() => setEditing(false)}
                    aria-label="Cancel"
                    className="focus-ring rounded-md p-2 text-[#71717a] hover:text-white"
                  >
                    <X className="h-4 w-4" aria-hidden />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <h1 className="truncate text-2xl font-bold tracking-tight text-white">{name}</h1>
                  {isAuthenticated && (
                    <button
                      ref={editBtnRef}
                      type="button"
                      onClick={beginEdit}
                      aria-label="Edit name"
                      className="focus-ring rounded-md p-1.5 text-[#a1a1aa] transition-colors hover:text-omnivra-cyan"
                    >
                      <Pencil className="h-4 w-4" aria-hidden />
                    </button>
                  )}
                </div>
              )}
              {nameErr && (
                <p role="alert" aria-live="polite" className="text-xs text-omnivra-pink">
                  {nameErr}
                </p>
              )}

              {email && <p className="truncate text-sm text-[#a1a1aa]">{email}</p>}

              <div className="mt-1 flex flex-wrap items-center justify-center gap-2 sm:justify-start">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-xs font-medium text-[#d4d4d8]">
                  <ProviderIcon provider={provider} />
                  {isAuthenticated ? `Signed in with ${providerLabel(provider)}` : 'Local admin'}
                </span>
                <StatusDot status="online" pulse label={isAuthenticated ? 'Active' : 'Open mode'} />
              </div>
            </div>

            {/* sign out (only when signed in) */}
            {isAuthenticated && (
              <div className="sm:self-start">
                <Button variant="outline" size="sm" onClick={handleSignOut}>
                  <LogOut className="h-4 w-4" aria-hidden />
                  Sign out
                </Button>
              </div>
            )}
          </div>
        </GlassCard>
      </Reveal>

      {/* ============ SIGNED-IN DETAILS ============ */}
      {isAuthenticated ? (
        <Stagger className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Account */}
          <StaggerItem>
            <GlassCard padding="md" className="flex h-full flex-col gap-1">
              <SectionHeader label="Account" />
              <div className="divide-y divide-white/[0.05]">
                <InfoRow icon={Mail} label="Email">
                  <span className="inline-flex items-center gap-1.5">
                    {email ?? '—'}
                    {verified && <BadgeCheck className="h-4 w-4 text-omnivra-emerald-bright" aria-label="Verified" />}
                  </span>
                </InfoRow>
                <InfoRow icon={UserRound} label="Member since">{formatDate(user?.created_at)}</InfoRow>
                <InfoRow icon={ShieldCheck} label="Last sign-in">{formatDate(user?.last_sign_in_at)}</InfoRow>
                <InfoRow icon={KeyRound} label="User ID">
                  <button
                    type="button"
                    onClick={copyId}
                    className="focus-ring inline-flex items-center gap-1.5 rounded font-mono text-xs text-[#a1a1aa] hover:text-white"
                    aria-label="Copy user ID"
                  >
                    <span className="max-w-[9rem] truncate">{user?.id ?? '—'}</span>
                    {copied ? <Check className="h-3.5 w-3.5 text-omnivra-emerald-bright" aria-hidden /> : <Copy className="h-3.5 w-3.5" aria-hidden />}
                  </button>
                </InfoRow>
              </div>
            </GlassCard>
          </StaggerItem>

          {/* Sign-in method */}
          <StaggerItem>
            <GlassCard padding="md" className="flex h-full flex-col gap-3">
              <SectionHeader label="Sign-in method" />
              <div className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-omnivra-surface-2">
                  <ProviderIcon provider={provider} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-zinc-100">{providerLabel(provider)}</p>
                  <p className="truncate text-xs text-zinc-400">{email ?? 'Connected'}</p>
                </div>
                <NeonBadge tone="success" dot>
                  Connected
                </NeonBadge>
              </div>
              <p className="text-xs leading-relaxed text-[#a1a1aa]">
                Your identity is managed by {providerLabel(provider)}. Email and avatar are read from there.
              </p>
            </GlassCard>
          </StaggerItem>

          {/* Quick actions */}
          <StaggerItem>
            <GlassCard padding="md" className="flex h-full flex-col gap-3">
              <SectionHeader label="Quick actions" />
              <div className="flex flex-col gap-2">
                <Link
                  to="/integrations"
                  className="focus-ring flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 transition-colors hover:border-white/15"
                >
                  <KeyRound className="h-4 w-4 text-omnivra-cyan" aria-hidden />
                  <span className="flex-1 text-sm text-[#e4e4e7]">Manage provider API keys</span>
                </Link>
                <Link
                  to="/settings"
                  className="focus-ring flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 transition-colors hover:border-white/15"
                >
                  <Sparkles className="h-4 w-4 text-omnivra-purple" aria-hidden />
                  <span className="flex-1 text-sm text-[#e4e4e7]">System settings</span>
                </Link>
              </div>
            </GlassCard>
          </StaggerItem>

          {/* Session */}
          <StaggerItem>
            <GlassCard padding="md" className="flex h-full flex-col gap-3">
              <SectionHeader label="Session" />
              <p className="text-xs leading-relaxed text-[#a1a1aa]">
                You’re signed in with {providerLabel(provider)}. Signing out clears your session on this device.
              </p>
              <Button variant="outline" onClick={handleSignOut} className="w-full">
                <LogOut className="h-4 w-4" aria-hidden />
                Sign out
              </Button>
            </GlassCard>
          </StaggerItem>
        </Stagger>
      ) : (
        /* ============ SIGNED-OUT / OPEN MODE ============ */
        <Reveal delay={0.05}>
          <GlassCard padding="lg" className="mx-auto flex w-full max-w-md flex-col items-center gap-5 text-center">
            <span className="grid h-12 w-12 place-items-center rounded-full bg-omnivra-surface-2 text-omnivra-cyan">
              <UserRound className="h-6 w-6" aria-hidden />
            </span>
            <div className="flex flex-col gap-1">
              <h2 className="text-lg font-semibold text-white">
                {isConfigured ? 'You’re not signed in' : 'Running in local admin mode'}
              </h2>
              <p className="max-w-sm text-sm text-[#a1a1aa]">
                {isConfigured
                  ? 'Sign in with Google or GitHub to personalize your profile and sync your identity.'
                  : 'Social sign-in is off. The app runs as a single local admin — enable Supabase to add profiles.'}
              </p>
            </div>
            {isConfigured ? (
              <OAuthButtons className="w-full" />
            ) : (
              <Link
                to="/integrations"
                className="focus-ring inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-omnivra-bg-root transition-transform hover:scale-[1.02]"
              >
                <KeyRound className="h-4 w-4" aria-hidden />
                Configure providers
              </Link>
            )}
          </GlassCard>
        </Reveal>
      )}
    </div>
  )
}
