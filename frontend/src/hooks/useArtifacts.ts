/**
 * Workspace artifact hooks (Phase 8).
 *  - useArtifacts(): the live artifact list, polled every 10s so a freshly-run
 *    workflow's outputs appear without a manual refresh.
 *  - useArtifact(path): the selected artifact's content, only fetched once a path
 *    is selected (enabled: !!path).
 * Both fail gracefully offline (jsdom/tests) — consumers default to [] / undefined
 * and render the empty state rather than crashing.
 */
import { useMutation, useQuery } from '@tanstack/react-query'
import { listArtifacts, readArtifact, runProgram } from '@/lib/api/artifacts'
import type { Artifact, ArtifactContent, RunProgramResult } from '@/lib/api/types'
import { useProjectStore } from '@/store/project'

/** Live artifact list — polled every 10s; scoped to the active project. */
export function useArtifacts() {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<Artifact[]>({
    queryKey: ['artifacts', projectId],
    queryFn: listArtifacts,
    refetchInterval: 10_000,
    retry: 1,
  })
}

/** The selected artifact's content; disabled until a path is chosen (scoped to project). */
export function useArtifact(path: string | null) {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<ArtifactContent>({
    queryKey: ['artifact', projectId, path],
    queryFn: () => readArtifact(path!),
    enabled: !!path,
  })
}

/** Run a generated workspace file in the guarded backend runner (returns its captured output). */
export function useRunProgram() {
  return useMutation<RunProgramResult, Error, string>({
    mutationFn: (path) => runProgram(path),
  })
}
