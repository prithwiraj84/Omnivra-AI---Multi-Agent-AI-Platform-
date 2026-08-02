/**
 * useMediaToken — keeps a fresh media token available to the URL builders.
 *
 * Mounted once at the app root. Fetches a short-lived, media-scoped token and refreshes it well
 * before expiry, so `<video>`, `<img>` and download links can authenticate (they can't send the
 * axios Authorization header). Harmless in open mode: the request simply yields nothing and the
 * builders emit plain URLs.
 */
import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'

import { fetchMediaToken, setMediaToken } from '@/lib/api/media-token'
import { useSupabaseAuth } from '@/hooks/useSupabaseAuth'

export function useMediaToken(): void {
  const { isAuthenticated, isConfigured } = useSupabaseAuth()

  const { data } = useQuery({
    queryKey: ['system', 'media-token', isAuthenticated],
    queryFn: fetchMediaToken,
    // Refresh comfortably inside the token's lifetime so a long session never serves a stale one.
    refetchInterval: 20 * 60 * 1000,
    refetchOnWindowFocus: true,
    staleTime: 15 * 60 * 1000,
    retry: 1,
    // In open mode there's no session to mint against; in per-user mode wait until signed in.
    enabled: !isConfigured || isAuthenticated,
  })

  useEffect(() => {
    setMediaToken(data?.token ?? null)
  }, [data])
}
