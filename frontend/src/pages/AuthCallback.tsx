/**
 * AuthCallback — the OAuth return page (/auth/callback). Supabase's detectSessionInUrl exchanges
 * the ?code=… for a session on load; this page watches the auth store and, once the session
 * materializes, forwards to /dashboard. It surfaces provider errors (e.g. access_denied) and a
 * "sign-in didn't complete" state instead of ever spinning forever.
 */
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertCircle, Loader2 } from 'lucide-react'

import { BrandLogo } from '@/components/layout/brand-logo'
import { GlassCard } from '@/components/ui/glass-card'
import { useSupabaseAuth } from '@/hooks/useSupabaseAuth'

/** Pull an OAuth error out of the callback URL (providers put it in the hash or the query). */
function readOAuthError(): string | null {
  if (typeof window === 'undefined') return null
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  const query = new URLSearchParams(window.location.search)
  return (
    hash.get('error_description') ||
    query.get('error_description') ||
    hash.get('error') ||
    query.get('error')
  )
}

export function AuthCallback() {
  const navigate = useNavigate()
  const { session, loading, isConfigured } = useSupabaseAuth()
  const oauthError = useMemo(readOAuthError, [])
  const [gaveUp, setGaveUp] = useState(false)

  // Success: session resolved → into the app.
  useEffect(() => {
    if (session) navigate('/dashboard', { replace: true })
  }, [session, navigate])

  // Nothing to do here if Supabase isn't set up.
  useEffect(() => {
    if (!isConfigured) navigate('/login', { replace: true })
  }, [isConfigured, navigate])

  // If the exchange settled with no session and no error, stop spinning after a short grace period.
  useEffect(() => {
    if (oauthError || session || loading) return
    const t = setTimeout(() => setGaveUp(true), 4000)
    return () => clearTimeout(t)
  }, [oauthError, session, loading])

  const failed = Boolean(oauthError) || gaveUp

  return (
    <div
      className="relative flex min-h-screen w-full items-center justify-center overflow-hidden p-6"
      style={{ backgroundColor: 'var(--omni-bg-base)' }}
    >
      <div aria-hidden className="pointer-events-none fixed inset-0 bg-grid-faint [background-size:32px_32px] opacity-60" />
      <div aria-hidden className="ambient-glow pointer-events-none fixed inset-x-0 top-0 h-[420px]" />

      <GlassCard variant="strong" padding="lg" className="relative z-10 w-full max-w-sm">
        <div className="flex flex-col items-center gap-6 text-center">
          <BrandLogo />
          {failed ? (
            <>
              <span className="grid h-11 w-11 place-items-center rounded-full bg-omnivra-red/10 text-omnivra-red">
                <AlertCircle className="h-5 w-5" aria-hidden />
              </span>
              <div className="flex flex-col gap-1" role="alert" aria-live="assertive">
                <h1 className="text-lg font-semibold text-white">Sign-in didn’t complete</h1>
                <p className="text-xs text-[#a1a1aa]">
                  {oauthError || 'We couldn’t establish a session. Please try again.'}
                </p>
              </div>
              <Link
                to="/login"
                className="focus-ring inline-flex h-10 w-full items-center justify-center rounded-md bg-white text-sm font-semibold text-omnivra-bg-root transition-transform hover:scale-[1.02] active:scale-95"
              >
                Back to sign in
              </Link>
            </>
          ) : (
            <>
              <Loader2 className="h-7 w-7 animate-spin text-omnivra-cyan" aria-hidden />
              <div className="flex flex-col gap-1" role="status" aria-live="polite">
                <h1 className="text-lg font-semibold text-white">Completing sign-in…</h1>
                <p className="text-xs text-[#71717a]">Securely establishing your session.</p>
              </div>
            </>
          )}
        </div>
      </GlassCard>
    </div>
  )
}
