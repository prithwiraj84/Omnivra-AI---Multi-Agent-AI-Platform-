/**
 * Supabase browser client (Phase 2 — Google/GitHub OAuth).
 *
 * The client is created ONLY when both VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are
 * present and non-placeholder; otherwise `supabase` is null and `isSupabaseConfigured` is
 * false. Every caller must guard on that so the app degrades gracefully to open mode when
 * Supabase isn't set up (local dev / tests / self-host without auth).
 *
 * The anon key is browser-safe by design (it only permits what your Row-Level-Security
 * policies allow). We use the PKCE flow with detectSessionInUrl so the OAuth redirect back
 * to /auth/callback is exchanged for a session automatically on load.
 */
import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const rawUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined
const rawKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined

/** True for empty / example-placeholder values ("your-project", "<anon-key>", …). */
function isPlaceholder(value?: string): boolean {
  if (!value) return true
  const v = value.trim()
  return v === '' || v.includes('your-') || v.includes('<') || v.includes('project-ref')
}

export const isSupabaseConfigured = !isPlaceholder(rawUrl) && !isPlaceholder(rawKey)

/** Where the OAuth provider sends the user back to (the callback finalizes the session). */
export function authRedirectTo(): string {
  return `${window.location.origin}/auth/callback`
}

export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(rawUrl as string, rawKey as string, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        flowType: 'pkce',
        storageKey: 'omnivra_supabase_auth',
      },
    })
  : null
