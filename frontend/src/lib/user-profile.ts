/**
 * Helpers to derive a friendly display identity from a Supabase user. Google/GitHub stash the
 * name + avatar under different `user_metadata` keys, so we normalize them here for the topbar,
 * the account menu, and the profile page (Phase 4).
 */
import type { User } from '@supabase/supabase-js'

/** Best-effort human name: full_name → name → github user_name → email local-part → "User". */
export function displayName(user: User | null | undefined): string {
  if (!user) return 'Guest'
  const m = (user.user_metadata ?? {}) as Record<string, unknown>
  const candidate =
    (m.full_name as string) ||
    (m.name as string) ||
    (m.user_name as string) ||
    (m.preferred_username as string) ||
    user.email?.split('@')[0] ||
    'User'
  return candidate
}

/** Provider avatar URL (Google `picture` / GitHub `avatar_url`), or null. */
export function avatarUrl(user: User | null | undefined): string | null {
  const m = (user?.user_metadata ?? {}) as Record<string, unknown>
  return ((m.avatar_url as string) || (m.picture as string) || null) as string | null
}

/** 1–2 letter initials for an avatar fallback. */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return 'U'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/** The OAuth provider that signed the user in ('google' | 'github' | 'email' | …). */
export function providerOf(user: User | null | undefined): string {
  if (!user) return 'email'
  const app = (user.app_metadata ?? {}) as { provider?: string }
  if (app.provider) return app.provider
  const first = user.identities?.[0]?.provider
  return first ?? 'email'
}

/** A human label for a provider id. */
export function providerLabel(provider: string): string {
  const map: Record<string, string> = { google: 'Google', github: 'GitHub', email: 'Email' }
  return map[provider] ?? provider.charAt(0).toUpperCase() + provider.slice(1)
}

/** Format an ISO timestamp as a short, locale-aware date (or '—' when absent/invalid). */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}
