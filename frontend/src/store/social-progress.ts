/**
 * Live social-generation progress (Zustand). Transient UI state fed by the /ws
 * 'social_progress' frames (see hooks/useWebSocket) and read by Social Studio to show
 * per-step progress (storyboard/voiceover for reels, caption/image for posts, and the
 * Pexels b-roll / MoviePy assemble steps at render) BEFORE the human-approval view.
 *
 * Keyed by jobId (the draft id). Each job accumulates its steps, deduped by `step` key so
 * a step's running -> done frames collapse to one row. Display is gated by the consumer
 * (composer panel while generating; reel card while rendering), so we only cap the map to
 * avoid unbounded growth across a long session.
 */
import { create } from 'zustand'
import type { SocialKind, SocialPhase, SocialProgressEvent, SocialProgressStatus } from '@/lib/api/types'

const MAX_JOBS = 24

export interface ProgressStep {
  step: string
  label: string
  status: SocialProgressStatus
  index: number
  detail?: string | null
}

export interface JobProgress {
  jobId: string
  projectId: string
  kind: SocialKind
  phase: SocialPhase
  total: number
  steps: ProgressStep[] // ordered by index; one row per step key (latest frame wins)
  updatedAt: number
}

interface SocialProgressState {
  byJob: Record<string, JobProgress>
  upsert: (e: SocialProgressEvent, now: number) => void
  clear: (jobId: string) => void
  /** Drop a project's finished draft-phase jobs (called when a new generation starts) so a
      prior completed checklist can't flash as if it were the new one. */
  clearDraftJobs: (projectId: string) => void
}

/** Merge one progress frame into a job: replace its step row (by key) and re-sort by index. */
function mergeStep(job: JobProgress, e: SocialProgressEvent, now: number): JobProgress {
  const row: ProgressStep = { step: e.step, label: e.label, status: e.status, index: e.index, detail: e.detail ?? null }
  const steps = job.steps.filter((s) => s.step !== e.step)
  steps.push(row)
  steps.sort((a, b) => a.index - b.index)
  // A later phase (render) supersedes the draft phase for the same job id.
  return { ...job, phase: e.phase, total: e.total, steps, updatedAt: now }
}

export const useSocialProgressStore = create<SocialProgressState>((set) => ({
  byJob: {},
  upsert: (e, now) =>
    set((state) => {
      const prev =
        state.byJob[e.jobId] && state.byJob[e.jobId].phase === e.phase
          ? state.byJob[e.jobId]
          : { jobId: e.jobId, projectId: e.projectId, kind: e.kind, phase: e.phase, total: e.total, steps: [], updatedAt: now }
      const byJob = { ...state.byJob, [e.jobId]: mergeStep(prev, e, now) }
      // Cap the map: drop the oldest jobs once we exceed MAX_JOBS.
      const ids = Object.keys(byJob)
      if (ids.length > MAX_JOBS) {
        const oldest = ids.sort((a, b) => byJob[a].updatedAt - byJob[b].updatedAt).slice(0, ids.length - MAX_JOBS)
        for (const id of oldest) delete byJob[id]
      }
      return { byJob }
    }),
  clear: (jobId) =>
    set((state) => {
      if (!state.byJob[jobId]) return state
      const byJob = { ...state.byJob }
      delete byJob[jobId]
      return { byJob }
    }),
  clearDraftJobs: (projectId) =>
    set((state) => {
      const byJob = { ...state.byJob }
      let changed = false
      for (const [id, j] of Object.entries(byJob)) {
        if (j.projectId === projectId && j.phase === 'draft') {
          delete byJob[id]
          changed = true
        }
      }
      return changed ? { byJob } : state
    }),
}))
