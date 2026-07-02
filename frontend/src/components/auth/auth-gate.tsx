import { Loader2 } from 'lucide-react'
import type { PropsWithChildren } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuthConfig } from '@/hooks/useAuth'
import { useSupabaseAuth } from '@/hooks/useSupabaseAuth'
import { useAuthStore } from '@/store/auth'

/**
 * AuthGate — guards the AppLayout-protected routes.
 *
 * Login is REQUIRED once auth is set up: whenever Supabase is configured (Google/GitHub OAuth)
 * OR the backend runs with AUTH_ENABLED. In that mode a visitor must present EITHER a Supabase
 * session OR a backend bearer token; otherwise they're redirected to "/login". With neither
 * configured (pure local dev), the app runs in open single-admin mode and always renders.
 *
 * "Never block forever / never flash private content": when auth is required but the Supabase
 * session (or the backend auth-config query) is still resolving, we show a loader rather than
 * either bouncing prematurely or rendering the app to a not-yet-known-unauthenticated visitor.
 * In jsdom/tests Supabase is unconfigured and AUTH_ENABLED is off, so the gate is a no-op.
 */
export function AuthGate({ children }: PropsWithChildren) {
  const { isLoading, isError } = useAuthConfig()
  const authEnabled = useAuthStore((s) => s.authEnabled)
  const token = useAuthStore((s) => s.token)
  const { isAuthenticated: supabaseAuthed, loading: supabaseLoading, isConfigured: supabaseConfigured } =
    useSupabaseAuth()

  const requireAuth = supabaseConfigured || authEnabled
  const hasAuth = Boolean(token) || supabaseAuthed

  if (requireAuth && !hasAuth) {
    // Still resolving the initial Supabase session, or the backend auth-config query → wait.
    const settlingSession = supabaseConfigured && supabaseLoading
    const settlingConfig = authEnabled && isLoading && !isError
    if (settlingSession || settlingConfig) {
      return (
        <div
          className="flex min-h-screen w-full items-center justify-center"
          style={{ backgroundColor: 'var(--omni-bg-base)' }}
          role="status"
          aria-label="Loading"
        >
          <Loader2 className="h-6 w-6 animate-spin text-[#71717a]" aria-hidden />
        </div>
      )
    }
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
