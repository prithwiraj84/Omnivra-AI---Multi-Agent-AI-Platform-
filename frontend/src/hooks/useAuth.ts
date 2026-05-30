/**
 * Auth hooks (Phase 10).
 *  - useAuthConfig(): fetches GET /auth/config once (staleTime Infinity) and mirrors the
 *    result into the auth store so the gate + Settings can read it synchronously. Offline
 *    (jsdom/tests) the query simply never resolves / fails — the app stays in open mode.
 *  - useLogin(): a mutation that, on success, records the token + username in the auth
 *    store (which also persists the token to localStorage for the axios interceptor).
 */
import { useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { getAuthConfig, login } from '@/lib/api/auth'
import type { AuthConfig, LoginResult } from '@/lib/api/auth'
import { useAuthStore } from '@/store/auth'

/** The server auth mode. Cached forever; folds `authEnabled` into the auth store. */
export function useAuthConfig() {
  const setAuthEnabled = useAuthStore((s) => s.setAuthEnabled)
  const query = useQuery<AuthConfig>({
    queryKey: ['auth', 'config'],
    queryFn: getAuthConfig,
    staleTime: Infinity,
    retry: 1,
  })

  useEffect(() => {
    if (query.data) setAuthEnabled(query.data.authEnabled)
  }, [query.data, setAuthEnabled])

  return query
}

interface LoginVars {
  username: string
  password: string
}

/** Sign in; on success stores the token + username (and persists the token). */
export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth)
  return useMutation<LoginResult, Error, LoginVars>({
    mutationFn: ({ username, password }) => login(username, password),
    onSuccess: (result) => {
      setAuth(result.token, result.username)
    },
  })
}
