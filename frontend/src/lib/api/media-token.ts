/**
 * Media token — lets BROWSER-NATIVE resource loads authenticate.
 *
 * `<video src>`, `<img src>` and download `<a href>` are fetched by the browser itself, which
 * cannot attach the axios `Authorization` header. Once the API required a signed-in user, every
 * one of those returned 401 — a black, unplayable video and a download that produced nothing.
 *
 * The backend mints a short-lived, MEDIA-SCOPED token (`GET /system/media-token`) that unlocks
 * only media + downloads, never the rest of the API. We keep the latest one in a module variable
 * (refreshed by `useMediaToken` at the app root) so the plain URL builders below can stay
 * synchronous, and append it as `?t=`.
 */
import { api } from '@/lib/api/client'

let _mediaToken: string | null = null

/** Store the freshest media token (called by the refresher hook). */
export function setMediaToken(token: string | null): void {
  _mediaToken = token
}

/** Fetch a new media token. Returns null when the endpoint is unavailable (open mode/offline). */
export async function fetchMediaToken(): Promise<{ token: string; expiresIn: number } | null> {
  try {
    const { data } = await api.get<{ token: string; expiresIn: number }>('/system/media-token')
    return data?.token ? data : null
  } catch {
    return null
  }
}

/**
 * Append the media token to a backend URL so the browser can load it.
 * No-op when we don't have one (open mode needs no auth), and safe on URLs that already have a
 * query string — every caller here builds one.
 */
export function withMediaToken(url: string): string {
  if (!_mediaToken) return url
  const sep = url.includes('?') ? '&' : '?'
  return `${url}${sep}t=${encodeURIComponent(_mediaToken)}`
}
