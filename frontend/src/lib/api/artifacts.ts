/**
 * Workspace artifact API calls (Phase 8). Uses the shared `@/lib/api/client`
 * axios instance (baseURL '/api'). Artifacts are the files agents wrote under
 * the path-jailed ./workspace sandbox.
 */
import { api } from '@/lib/api/client'
import type { Artifact, ArtifactContent, RunProgramResult } from '@/lib/api/types'

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

/**
 * Run a generated workspace file in the guarded backend runner. POST /workspace/run.
 * A longer per-call timeout (the backend caps the run at 15s) overrides the 10s default.
 */
export async function runProgram(path: string): Promise<RunProgramResult> {
  const { data } = await api.post<RunProgramResult>('/workspace/run', { path }, { timeout: 30_000 })
  return data
}

/** Extensions the guarded runner can execute (mirrors backend code_runner). */
export const RUNNABLE_EXTENSIONS = ['.py', '.js', '.mjs']

/** True if a workspace path can be run by the backend (.py/.js/.mjs). */
export function isRunnable(path: string): boolean {
  return RUNNABLE_EXTENSIONS.some((ext) => path.toLowerCase().endsWith(ext))
}
