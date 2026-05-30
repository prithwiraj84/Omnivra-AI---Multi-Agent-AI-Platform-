import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { Lock, LogIn, User } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { Button } from '@/components/ui/button'
import { BrandLogo } from '@/components/layout/brand-logo'
import { Reveal } from '@/components/common/reveal'
import { useLogin } from '@/hooks/useAuth'

/** Map a login failure to an on-brand message (401 -> bad creds, else generic). */
function loginErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error) && error.response?.status === 401) {
    return 'Invalid username or password.'
  }
  return 'Could not sign in. Check the server and try again.'
}

/**
 * Login — the centered glass sign-in card shown when auth is enabled and the user
 * has no token (see AuthGate). On success it navigates to "/". On-brand dark/neon:
 * the OMNIVRA mark over username + password fields and a primary "Sign in" button.
 * In open mode any credentials are accepted by the backend.
 */
export function Login() {
  const navigate = useNavigate()
  const loginMutation = useLogin()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    loginMutation.mutate(
      { username: username.trim(), password },
      { onSuccess: () => navigate('/', { replace: true }) },
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
      <GlassCard variant="strong" padding="lg" className="w-full">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <BrandLogo />
            <div className="flex flex-col gap-1">
              <h1 className="text-lg font-semibold text-white">Sign in to OMNIVRA</h1>
              <p className="text-xs text-[#71717a]">
                Enter your credentials to access the AI Company OS.
              </p>
            </div>
          </div>

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
