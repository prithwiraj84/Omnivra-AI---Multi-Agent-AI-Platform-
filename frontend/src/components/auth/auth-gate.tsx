import { Loader2 } from 'lucide-react'
import type { PropsWithChildren } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuthConfig } from '@/hooks/useAuth'
import { useAuthStore } from '@/store/auth'

/**
 * AuthGate — guards the AppLayout-protected routes.
 *
 *  - Open mode (authEnabled === false, the default): always renders children.
 *  - Enabled mode with no token in the auth store: redirects to "/login".
 *  - Otherwise renders children.
 *
 * The decision keys on the store's `authEnabled` (seeded false, set true only once
 * GET /auth/config confirms it). This is the crucial "never block forever" property:
 * while the config query is pending — and in jsdom/tests where it never resolves or
 * fails — the store stays in open mode (false), so children render immediately and we
 * never redirect. A loader appears only in the narrow window where we already know
 * auth is enabled but are still confirming the token/config (it never gates open mode).
 */
export function AuthGate({ children }: PropsWithChildren) {
  const { isLoading, isError } = useAuthConfig()
  const authEnabled = useAuthStore((s) => s.authEnabled)
  const token = useAuthStore((s) => s.token)

  if (authEnabled && !token) {
    return <Navigate to="/login" replace />
  }

  // Show a minimal loader only while auth is enabled and the config is still settling
  // (e.g. a token holder re-validating). Open mode and any settled/failed state fall
  // straight through to children, so we never hang.
  if (authEnabled && isLoading && !isError) {
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
