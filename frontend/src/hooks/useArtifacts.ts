/**
 * Workspace artifact hooks (Phase 8).
 *  - useArtifacts(): the live artifact list, polled every 10s so a freshly-run
 *    workflow's outputs appear without a manual refresh.
 *  - useArtifact(path): the selected artifact's content, only fetched once a path
 *    is selected (enabled: !!path).
 * Both fail gracefully offline (jsdom/tests) — consumers default to [] / undefined
 * and render the empty state rather than crashing.
 */
import { useQuery } from '@tanstack/react-query'
import { listArtifacts, readArtifact } from '@/lib/api/artifacts'
import type { Artifact, ArtifactContent } from '@/lib/api/types'

/** Live artifact list — polled every 10s; one retry so an offline host settles quickly. */
export function useArtifacts() {
  return useQuery<Artifact[]>({
    queryKey: ['artifacts'],
    queryFn: listArtifacts,
    refetchInterval: 10_000,
    retry: 1,
  })
}

/** The selected artifact's content; disabled until a path is chosen. */
export function useArtifact(path: string | null) {
  return useQuery<ArtifactContent>({
    queryKey: ['artifact', path],
    queryFn: () => readArtifact(path!),
    enabled: !!path,
  })
}
