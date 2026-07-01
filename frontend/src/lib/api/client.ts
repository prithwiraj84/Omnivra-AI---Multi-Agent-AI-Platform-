/** Axios instance for the Omnivra backend.
 *  - Dev: Vite proxies /api -> :8000 (see vite.config.ts), so the default '/api' works same-origin.
 *  - Prod (Vercel -> a remote backend like a HF Space): set VITE_API_BASE_URL to the backend's
 *    absolute /api base (e.g. https://<user>-<space>.hf.space/api) so cross-origin calls resolve. */
import axios from 'axios'
import { TOKEN_STORAGE_KEY } from '@/store/auth'
import { getActiveProjectId } from '@/store/project'

// VITE_API_BASE_URL is the backend ORIGIN (e.g. http://localhost:8000 or https://<space>.hf.space).
// Empty in dev -> same-origin '/api' via the Vite proxy. We tolerate a value that already ends in
// '/api' (either convention works) and never double up the prefix.
const _raw = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '') || ''
/** Backend origin WITHOUT the /api suffix — for root routes like /health. '' in dev (root-relative). */
export const backendOrigin = _raw.endsWith('/api') ? _raw.slice(0, -4) : _raw
/** Absolute `/api` base for axios. Dev: '/api' (Vite proxy). Prod: '<origin>/api'. */
export const API_BASE_URL = backendOrigin ? `${backendOrigin}/api` : '/api'

/** Build an absolute backend URL for an /api path used OUTSIDE axios (<a href>, <img src>). */
export const apiUrl = (path: string): string => `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`

export const api = axios.create({
  baseURL: API_BASE_URL,
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
