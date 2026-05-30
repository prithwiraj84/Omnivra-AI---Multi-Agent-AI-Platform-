/**
 * Agent roster API calls. Uses the shared `@/lib/api/client` axios instance
 * (baseURL '/api'). The roster is the same shape as the bundled `AGENTS`
 * fallback in `@/config/agents`, so the UI can render instantly offline and
 * upgrade to the live list when GET /agents responds.
 */
import { api } from '@/lib/api/client'
import type { AgentSummary } from '@/types'

/** List every registered agent (23 total). GET /agents. */
export async function listAgents(): Promise<AgentSummary[]> {
  const { data } = await api.get<AgentSummary[]>('/agents')
  return data
}
