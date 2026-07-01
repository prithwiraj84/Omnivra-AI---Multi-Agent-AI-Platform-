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
