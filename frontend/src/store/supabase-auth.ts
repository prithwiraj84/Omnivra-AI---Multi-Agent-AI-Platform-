/**
 * Supabase auth state (Zustand) — the signed-in identity from Google/GitHub OAuth.
 *
 * This is a separate concern from the backend bearer-token store (store/auth.ts): it carries
 * WHO the visitor is (for the profile + a personalized topbar), while the backend store carries
 * the API access token. `loading` is true only until the initial session is resolved; when
 * Supabase isn't configured it starts false so nothing ever waits on it.
 *
 * The listener is installed once by useInitSupabaseAuth() (mounted at the app root) — this store
 * just holds the latest snapshot pushed in by getSession() + onAuthStateChange.
 */
import { create } from 'zustand'
import type { Session, User } from '@supabase/supabase-js'

import { isSupabaseConfigured } from '@/lib/supabase'

interface SupabaseAuthState {
  /** The current Supabase session (null when signed out / unconfigured). */
  session: Session | null
  /** Convenience mirror of session.user. */
  user: User | null
  /** True until the initial session has been resolved (false immediately when unconfigured). */
  loading: boolean
  /** Push a new session snapshot (also flips `loading` off). */
  setSession: (session: Session | null) => void
}

export const useSupabaseAuthStore = create<SupabaseAuthState>((set) => ({
  session: null,
  user: null,
  // Only "load" when there's a client that could produce a session.
  loading: isSupabaseConfigured,
  setSession: (session) => set({ session, user: session?.user ?? null, loading: false }),
}))
