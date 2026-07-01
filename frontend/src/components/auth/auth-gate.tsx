import { Loader2 } from 'lucide-react'
import type { PropsWithChildren } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuthConfig } from '@/hooks/useAuth'
import { useSupabaseAuth } from '@/hooks/useSupabaseAuth'
import { useAuthStore } from '@/store/auth'

/**
 * AuthGate — guards the AppLayout-protected routes.
 *
 *  - Open mode (authEnabled === false, the default): always renders children.
 *  - Enabled mode: renders children when EITHER a backend bearer token OR a Supabase OAuth
 *    session is present; otherwise redirects to "/login".
 *  - Otherwise renders children.
 *
 * The decision keys on the store's `authEnabled` (seeded false, set true only once
 * GET /auth/config confirms it). This is the crucial "never block forever" property:
 * while the config query is pending — and in jsdom/tests where it never resolves or
 * fails — the store stays in open mode (false), so children render immediately and we
 * never redirect.
 *
 * A Supabase session counts as satisfying the gate so that "sign in with Google/GitHub"
 * actually grants app access (and so an OAuth user can never be bounced into an infinite
 * /login ↔ /dashboard loop). We only accept it as MORE permissive — a session is never
 * REQUIRED, so open mode still lets everyone in. A loader appears only in the narrow window
 * where auth is enabled, there's no token yet, and we're still confirming the config or the
 * initial Supabase session.
 */
export function AuthGate({ children }: PropsWithChildren) {
  const { isLoading, isError } = useAuthConfig()
  const authEnabled = useAuthStore((s) => s.authEnabled)
  const token = useAuthStore((s) => s.token)
  const { isAuthenticated: supabaseAuthed, loading: supabaseLoading, isConfigured: supabaseConfigured } =
    useSupabaseAuth()

  // A backend token or a Supabase session satisfies the gate.
  if (authEnabled && !token && !supabaseAuthed) {
    // If Supabase is set up but its session is still resolving, wait rather than redirect —
    // a valid OAuth session may be about to arrive.
    const settlingSession = supabaseConfigured && supabaseLoading
    const settlingConfig = isLoading && !isError
    if (!settlingSession && !settlingConfig) {
      return <Navigate to="/login" replace />
    }
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

  return <>{children}</>
}
