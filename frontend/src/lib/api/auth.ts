/**
 * Auth API calls (Phase 10). Uses the shared `@/lib/api/client` axios instance
 * (baseURL '/api'). Mirrors backend app/api/routes/auth.py mounted at /api/auth:
 *  - GET  /auth/config -> { authEnabled }
 *  - POST /auth/login  -> { token, username }
 *  - GET  /auth/me     -> { username }   (requires a valid token when auth is enabled)
 */
import { api } from '@/lib/api/client'

/** Wire shape of GET /auth/config. */
export interface AuthConfig {
  authEnabled: boolean
}

/** Wire shape of POST /auth/login. */
export interface LoginResult {
  token: string
  username: string
}

/** Wire shape of GET /auth/me. */
export interface Me {
  username: string
}

/** Whether the backend requires a login. GET /auth/config. */
export async function getAuthConfig(): Promise<AuthConfig> {
  const { data } = await api.get<AuthConfig>('/auth/config')
  return data
}

/** Exchange credentials for a bearer token. POST /auth/login. */
export async function login(username: string, password: string): Promise<LoginResult> {
  const { data } = await api.post<LoginResult>('/auth/login', { username, password })
  return data
}

/** Identify the current caller (requires a valid token when auth is enabled). GET /auth/me. */
export async function me(): Promise<Me> {
  const { data } = await api.get<Me>('/auth/me')
  return data
}
