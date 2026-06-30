import { ArtifactExplorer } from '@/components/workspace/artifact-explorer'
import { AppRunnerPanel } from '@/components/workspace/app-runner-panel'

/**
 * Workspace — generated apps you can RUN/DOWNLOAD with one click (universal runner), plus the
 * artifact explorer over the full ./workspace sandbox (frontend/backend/docs/presentations/reports).
 */
export function Workspace() {
  return (
    <div className="flex flex-col gap-5">
      <AppRunnerPanel />
      <ArtifactExplorer title="Workspace Artifacts" />
    </div>
  )
}
