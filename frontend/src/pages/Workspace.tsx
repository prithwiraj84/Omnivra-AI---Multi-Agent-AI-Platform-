import { ArtifactExplorer } from '@/components/workspace/artifact-explorer'

/**
 * Workspace — the artifact explorer over the full ./workspace sandbox
 * (all categories: frontend/backend/docs/presentations/reports).
 */
export function Workspace() {
  return <ArtifactExplorer title="Workspace Artifacts" />
}
