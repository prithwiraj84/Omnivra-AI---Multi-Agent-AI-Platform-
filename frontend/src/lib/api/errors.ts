/**
 * Turning an API failure into a message that points at the right fix.
 *
 * The three cases need three different reactions, and conflating them wastes the user's time:
 *   - TIMEOUT      the server is fine and probably still working; wait / retry
 *   - NO RESPONSE  nothing answered — the backend really is unreachable
 *   - HTTP ERROR   the server explained itself; show its `detail`
 * Long generations used to hit the first case and report the second ("Is the backend running?"),
 * sending people to check a server that was working perfectly.
 */
import axios from 'axios'

export function isTimeout(error: unknown): boolean {
  return (
    axios.isAxiosError(error) &&
    !error.response &&
    (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT' || /timeout/i.test(error.message ?? ''))
  )
}

/**
 * A user-facing message for a failed request.
 * `action` names what was being attempted, e.g. "generate the document".
 */
export function apiErrorMessage(error: unknown, action: string): string {
  if (isTimeout(error)) {
    return `Taking longer than expected to ${action}. The server is still working — wait a moment and refresh, or try again.`
  }
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail
    if (detail) return detail
    if (!error.response) return `Could not reach the server to ${action}. Is the backend running?`
    if (error.response.status === 401) return 'Your session expired. Please sign in again.'
    if (error.response.status === 429) return `Rate limited while trying to ${action}. Try again shortly.`
  }
  return `Could not ${action}. Please try again.`
}
