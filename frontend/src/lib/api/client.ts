/** Axios instance for the Omnivra backend.
 *  - Dev: Vite proxies /api -> :8000 (see vite.config.ts), so the default '/api' works same-origin.
 *  - Prod (Vercel -> a remote backend like a HF Space): set VITE_API_BASE_URL to the backend's
 *    absolute /api base (e.g. https://<user>-<space>.hf.space/api) so cross-origin calls resolve. */
import axios from 'axios'
import { supabase } from '@/lib/supabase'
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
 * Attach the auth token to every request. Prefer the **Supabase access token** (the backend
 * verifies it to identify the user for per-user private workspaces), auto-refreshed by
 * supabase-js; fall back to the legacy backend token in localStorage for open/self-host mode.
 * Async so we can read the freshest Supabase session. Harmless in open mode (no token).
 */
api.interceptors.request.use(async (config) => {
  let bearer: string | null = null
  if (supabase) {
    try {
      const { data } = await supabase.auth.getSession()
      bearer = data.session?.access_token ?? null
    } catch {
      bearer = null
    }
  }
  if (!bearer) {
    try {
      bearer = localStorage.getItem(TOKEN_STORAGE_KEY)
    } catch {
      bearer = null
    }
  }
  if (bearer) {
    config.headers.set('Authorization', `Bearer ${bearer}`)
  }
  // Scope every request to the active project (backend stores are partitioned by it).
  config.headers.set('X-Project-Id', getActiveProjectId())
  return config
})
