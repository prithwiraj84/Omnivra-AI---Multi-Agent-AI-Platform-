import axios from 'axios'
import { ArrowLeft, Lock, LogIn, User } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { OAuthButtons } from '@/components/auth/oauth-buttons'
import { Reveal } from '@/components/common/reveal'
import { BrandLogo } from '@/components/layout/brand-logo'
import { Button } from '@/components/ui/button'
import { GlassCard } from '@/components/ui/glass-card'
import { useLogin } from '@/hooks/useAuth'
import { useSupabaseAuth } from '@/hooks/useSupabaseAuth'

/** Map a login failure to an on-brand message (401 -> bad creds, else generic). */
function loginErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error) && error.response?.status === 401) {
    return 'Invalid username or password.'
  }
  return 'Could not sign in. Check the server and try again.'
}

/**
 * Login — the public sign-in page. Google/GitHub OAuth (Supabase) is the primary path; a
 * username/password form remains below as a fallback for open/self-host mode. If a Supabase
 * session already exists we forward straight to the app. On credential success we navigate to
 * /dashboard.
 */
export function Login() {
  const navigate = useNavigate()
  const loginMutation = useLogin()
  const { isAuthenticated } = useSupabaseAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  // Already signed in with Google/GitHub → skip the form.
  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard', { replace: true })
  }, [isAuthenticated, navigate])

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    loginMutation.mutate(
      { username: username.trim(), password },
      { onSuccess: () => navigate('/dashboard', { replace: true }) },
    )
  }

  return (
    <div
      className="relative flex min-h-screen w-full items-center justify-center overflow-hidden p-6"
      style={{ backgroundColor: 'var(--omni-bg-base)' }}
    >
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 bg-grid-faint [background-size:32px_32px] opacity-60"
      />
      <div
        aria-hidden
        className="ambient-glow pointer-events-none fixed inset-x-0 top-0 h-[420px]"
      />

      <Reveal y={18} className="relative z-10 w-full max-w-sm">
        <Link
          to="/"
          className="focus-ring mb-4 inline-flex items-center gap-1.5 rounded-md text-xs font-medium text-[#a1a1aa] transition-colors hover:text-white"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Back to home
        </Link>
        <GlassCard variant="strong" padding="lg" className="w-full">
          <div className="flex flex-col gap-6">
            <div className="flex flex-col items-center gap-4 text-center">
              <BrandLogo />
              <div className="flex flex-col gap-1">
                <h1 className="text-lg font-semibold text-white">Sign in to OMNIVRA</h1>
                <p className="text-xs text-[#71717a]">
                  Access your AI Company OS. Use Google or GitHub to get started.
                </p>
              </div>
            </div>

            {/* Primary: social OAuth via Supabase */}
            <OAuthButtons />

            {/* Divider */}
            <div className="flex items-center gap-3" aria-hidden>
              <span className="h-px flex-1 bg-white/[0.08]" />
              <span className="text-[11px] font-medium uppercase tracking-wide text-[#71717a]">
                or with credentials
              </span>
              <span className="h-px flex-1 bg-white/[0.08]" />
            </div>

            {/* Fallback: username/password (open / self-host mode) */}
            <form className="flex flex-col gap-4" onSubmit={onSubmit}>
              <label className="flex flex-col gap-1.5">
                <span className="section-label">Username</span>
                <div className="relative flex items-center">
                  <User
                    className="pointer-events-none absolute left-3 h-[18px] w-[18px] text-[#71717a]"
                    aria-hidden
                  />
                  <input
                    type="text"
                    autoComplete="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="admin"
                    aria-label="Username"
                    className="focus-ring h-10 w-full rounded-md bg-omnivra-surface-2 pl-10 pr-3 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
                  />
                </div>
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="section-label">Password</span>
                <div className="relative flex items-center">
                  <Lock
                    className="pointer-events-none absolute left-3 h-[18px] w-[18px] text-[#71717a]"
                    aria-hidden
                  />
                  <input
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    aria-label="Password"
                    className="focus-ring h-10 w-full rounded-md bg-omnivra-surface-2 pl-10 pr-3 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
                  />
                </div>
              </label>

              {loginMutation.isError && (
                <p className="text-xs text-omnivra-pink" role="alert" aria-live="polite">
                  {loginErrorMessage(loginMutation.error)}
                </p>
              )}

              <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
                <LogIn aria-hidden />
                {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
              </Button>
            </form>
          </div>
        </GlassCard>
      </Reveal>
    </div>
  )
}
