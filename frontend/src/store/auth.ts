/**
 * Auth state (Zustand). Holds the bearer token + the logged-in username and the
 * server's auth mode (authEnabled). The token is persisted to localStorage under
 * `omnivra_token` so it survives reloads and the axios request interceptor
 * (see lib/api/client) can read it; the store seeds its initial token from there.
 *
 * In open mode (authEnabled === false, the default) the app never requires a token,
 * so the store simply carries whatever /auth/login handed back (if anything).
 */
import { create } from 'zustand'

/** localStorage key the token is persisted under (shared with the axios interceptor). */
export const TOKEN_STORAGE_KEY = 'omnivra_token'

/** Read the persisted token, tolerating environments without localStorage (SSR/tests). */
function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

/** Persist (or clear) the token, tolerating environments without localStorage. */
function writeStoredToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token)
    else localStorage.removeItem(TOKEN_STORAGE_KEY)
  } catch {
    /* no-op: localStorage unavailable (private mode / jsdom) */
  }
}

interface AuthState {
  /** Bearer token (null when none has been issued / open mode without login). */
  token: string | null
  /** The logged-in username (null until login). */
  username: string | null
  /** Whether the backend requires authentication (from GET /auth/config). */
  authEnabled: boolean
  /** Record a successful login: stores token + username and persists the token. */
  setAuth: (token: string, username: string) => void
  /** Forget the session: clears token + username and removes the persisted token. */
  clearAuth: () => void
  /** Record the server's auth mode (from the auth-config query). */
  setAuthEnabled: (enabled: boolean) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: readStoredToken(),
  username: null,
  authEnabled: false,
  setAuth: (token, username) => {
    writeStoredToken(token)
    set({ token, username })
  },
  clearAuth: () => {
    writeStoredToken(null)
    set({ token: null, username: null })
  },
  setAuthEnabled: (enabled) => set({ authEnabled: enabled }),
}))
