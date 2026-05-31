/** Axios instance for the Omnivra backend. Vite proxies /api and /ws to :8000 (see vite.config.ts). */
import axios from 'axios'
import { TOKEN_STORAGE_KEY } from '@/store/auth'
import { getActiveProjectId } from '@/store/project'

export const api = axios.create({
  baseURL: '/api',
  timeout: 10_000,
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Attach the bearer token (when present) to every request. We read it straight from
 * localStorage rather than the store so this stays a plain module with no React/store
 * coupling — the auth store keeps the same key in sync. Harmless in open mode (no token).
 */
api.interceptors.request.use((config) => {
  let token: string | null = null
  try {
    token = localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    token = null
  }
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  // Scope every request to the active project (backend stores are partitioned by it).
  config.headers.set('X-Project-Id', getActiveProjectId())
  return config
})
