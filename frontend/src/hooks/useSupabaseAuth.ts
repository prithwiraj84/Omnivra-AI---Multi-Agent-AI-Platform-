/**
 * Supabase auth hooks (Phase 2 — Google/GitHub OAuth).
 *
 *  - useInitSupabaseAuth(): install ONCE at the app root. Seeds the store from getSession()
 *    and subscribes to onAuthStateChange so the whole app reacts to sign-in / sign-out /
 *    token-refresh. A no-op (marks not-loading) when Supabase isn't configured.
 *  - useSupabaseAuth(): read the current identity + the sign-in / sign-out actions.
 */
import { useCallback, useEffect } from 'react'

import { authRedirectTo, isSupabaseConfigured, supabase } from '@/lib/supabase'
import { useSupabaseAuthStore } from '@/store/supabase-auth'

export type OAuthProvider = 'google' | 'github'

/** Install the auth listener once (call at the app root). */
export function useInitSupabaseAuth(): void {
  const setSession = useSupabaseAuthStore((s) => s.setSession)

  useEffect(() => {
    if (!supabase) {
      setSession(null) // unconfigured → resolve immediately, stay in open mode
      return
    }
    let active = true
    supabase.auth
      .getSession()
      .then(({ data }) => {
        if (active) setSession(data.session)
      })
      .catch(() => {
        if (active) setSession(null)
      })

    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })
    return () => {
      active = false
      data.subscription.unsubscribe()
    }
  }, [setSession])
}

/** Read the signed-in identity + expose the OAuth sign-in / sign-out actions. */
export function useSupabaseAuth() {
  const session = useSupabaseAuthStore((s) => s.session)
  const user = useSupabaseAuthStore((s) => s.user)
  const loading = useSupabaseAuthStore((s) => s.loading)

  /** Kick off an OAuth redirect (browser navigates away to the provider). */
  const signInWithProvider = useCallback(async (provider: OAuthProvider) => {
    if (!supabase) throw new Error('Supabase is not configured')
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: authRedirectTo() },
    })
    if (error) throw error
  }, [])

  const signOut = useCallback(async () => {
    if (!supabase) return
    await supabase.auth.signOut()
  }, [])

  return {
    session,
    user,
    loading,
    isConfigured: isSupabaseConfigured,
    isAuthenticated: Boolean(user),
    signInWithProvider,
    signOut,
  }
}
