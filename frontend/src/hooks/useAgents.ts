/**
 * useAgents — the single source of agent-roster data for the UI.
 * Renders instantly from the bundled `AGENTS` fallback (initialData), then
 * upgrades to the live backend list from GET /agents when the API responds.
 * Offline (or in tests) it stays on the fallback so the page never blanks out.
 */
import { useQuery } from '@tanstack/react-query'
import { listAgents } from '@/lib/api/agents'
import { AGENTS } from '@/config/agents'
import type { AgentSummary } from '@/types'

export function useAgents() {
  return useQuery<AgentSummary[]>({
    queryKey: ['agents'],
    queryFn: listAgents,
    initialData: AGENTS,
    staleTime: 30_000,
    retry: 1,
  })
}
