/**
 * OAuthButtons — "Continue with Google / GitHub" via Supabase OAuth. Clicking kicks off a
 * redirect to the provider (the browser navigates away). Disabled with a hint when Supabase
 * isn't configured; shows a friendly error if the provider isn't enabled in the project.
 */
import { useState } from 'react'
import { Github, Loader2 } from 'lucide-react'

import { useSupabaseAuth, type OAuthProvider } from '@/hooks/useSupabaseAuth'
import { cn } from '@/lib/utils'

/** Google's multicolor "G" mark. */
export function GoogleMark() {
  return (
    <svg viewBox="0 0 24 24" className="h-[18px] w-[18px]" aria-hidden>
      <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.24 1.5-1.7 4.4-5.5 4.4-3.3 0-6-2.7-6-6.1s2.7-6.1 6-6.1c1.9 0 3.2.8 3.9 1.5l2.7-2.6C16.9 3 14.7 2 12 2 6.9 2 2.8 6.1 2.8 12S6.9 22 12 22c6.1 0 8.4-4.3 8.4-6.5 0-.4 0-.7-.1-1.1H12z" />
      <path fill="#4285F4" d="M21.9 14.4c.1-.4.1-.9.1-1.4 0-.5 0-.8-.1-1.1H12v3.9h5.5c-.1.8-.6 1.9-1.5 2.6l2.7 2.1c1.6-1.5 2.6-3.7 3.2-6.1z" />
      <path fill="#FBBC05" d="M6 14.3c-.2-.6-.3-1.2-.3-1.9s.1-1.3.3-1.9L3.3 8.4C2.6 9.7 2.2 11.3 2.2 12.9s.4 3.2 1.1 4.5L6 14.3z" />
      <path fill="#34A853" d="M12 22c2.4 0 4.5-.8 6-2.2l-2.7-2.1c-.8.5-1.8.9-3.3.9-2.5 0-4.6-1.7-5.4-4L3.9 16.6C5.3 19.8 8.4 22 12 22z" />
    </svg>
  )
}

export function OAuthButtons({ className }: { className?: string }) {
  const { isConfigured, signInWithProvider } = useSupabaseAuth()
  const [pending, setPending] = useState<OAuthProvider | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function go(provider: OAuthProvider) {
    setError(null)
    setPending(provider)
    try {
      await signInWithProvider(provider) // browser redirects away on success
    } catch {
      setError('Could not start sign-in. Make sure this provider is enabled in your Supabase project.')
      setPending(null)
    }
  }

  const base =
    'focus-ring inline-flex h-11 w-full items-center justify-center gap-2.5 rounded-xl border border-white/10 bg-white/[0.04] px-5 text-sm font-semibold text-white backdrop-blur-glass transition-colors hover:border-white/25 disabled:cursor-not-allowed disabled:opacity-50'

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <button type="button" onClick={() => go('google')} disabled={!isConfigured || pending !== null} className={base}>
        {pending === 'google' ? <Loader2 className="h-[18px] w-[18px] animate-spin" aria-hidden /> : <GoogleMark />}
        Continue with Google
      </button>
      <button type="button" onClick={() => go('github')} disabled={!isConfigured || pending !== null} className={base}>
        {pending === 'github' ? (
          <Loader2 className="h-[18px] w-[18px] animate-spin" aria-hidden />
        ) : (
          <Github className="h-[18px] w-[18px]" aria-hidden />
        )}
        Continue with GitHub
      </button>

      {!isConfigured && (
        <p className="text-center text-[11px] text-[#71717a]">
          Social sign-in is off — set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to enable it.
        </p>
      )}
      {error && (
        <p role="alert" aria-live="polite" className="text-center text-xs text-omnivra-pink">
          {error}
        </p>
      )}
    </div>
  )
}
