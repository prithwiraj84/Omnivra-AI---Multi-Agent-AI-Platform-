/**
 * Workspace artifact API calls (Phase 8). Uses the shared `@/lib/api/client`
 * axios instance (baseURL '/api'). Artifacts are the files agents wrote under
 * the path-jailed ./workspace sandbox.
 */
import { api } from '@/lib/api/client'
import type { Artifact, ArtifactContent } from '@/lib/api/types'

/** List every artifact under the workspace sandbox (newest first). GET /workspace/artifacts. */
export async function listArtifacts(): Promise<Artifact[]> {
  const { data } = await api.get<Artifact[]>('/workspace/artifacts')
  return data
}

/**
 * Read one artifact's text content. GET /workspace/artifacts/{path}. The path is
 * encoded segment-by-segment so nested paths (e.g. "docs/spec.md") stay intact
 * while still escaping any unsafe characters.
 */
export async function readArtifact(path: string): Promise<ArtifactContent> {
  const encoded = path.split('/').map(encodeURIComponent).join('/')
  const { data } = await api.get<ArtifactContent>(`/workspace/artifacts/${encoded}`)
  return data
}
