import { afterEach, describe, expect, it } from 'vitest'
import { useSocialProgressStore } from '@/store/social-progress'
import type { SocialProgressEvent } from '@/lib/api/types'

function evt(over: Partial<SocialProgressEvent> = {}): SocialProgressEvent {
  return {
    jobId: 'reel_1',
    projectId: 'p1',
    kind: 'reel',
    phase: 'draft',
    step: 'storyboard',
    label: 'Writing…',
    status: 'running',
    index: 1,
    total: 3,
    detail: null,
    ...over,
  }
}

afterEach(() => useSocialProgressStore.setState({ byJob: {} }))

describe('social-progress store', () => {
  it('collapses a step’s running -> done frames into one row (latest wins)', () => {
    const { upsert } = useSocialProgressStore.getState()
    upsert(evt({ step: 'storyboard', status: 'running', index: 1 }), 1)
    upsert(evt({ step: 'storyboard', status: 'done', index: 1, detail: '5 scenes' }), 2)
    const job = useSocialProgressStore.getState().byJob['reel_1']
    expect(job.steps).toHaveLength(1)
    expect(job.steps[0].status).toBe('done')
    expect(job.steps[0].detail).toBe('5 scenes')
  })

  it('orders steps by index regardless of arrival order', () => {
    const { upsert } = useSocialProgressStore.getState()
    upsert(evt({ step: 'voiceover', index: 2 }), 1)
    upsert(evt({ step: 'storyboard', index: 1 }), 2)
    upsert(evt({ step: 'ready', index: 3, status: 'done' }), 3)
    const steps = useSocialProgressStore.getState().byJob['reel_1'].steps
    expect(steps.map((s) => s.step)).toEqual(['storyboard', 'voiceover', 'ready'])
  })

  it('starts a fresh step list when the same job moves from draft to render phase', () => {
    const { upsert } = useSocialProgressStore.getState()
    upsert(evt({ phase: 'draft', step: 'ready', index: 3, status: 'done', total: 3 }), 1)
    upsert(evt({ phase: 'render', step: 'broll', index: 1, status: 'running', total: 4 }), 2)
    const job = useSocialProgressStore.getState().byJob['reel_1']
    expect(job.phase).toBe('render')
    expect(job.total).toBe(4)
    expect(job.steps.map((s) => s.step)).toEqual(['broll']) // draft steps not carried over
  })

  it('caps the map and drops the oldest jobs', () => {
    const { upsert } = useSocialProgressStore.getState()
    for (let i = 0; i < 30; i++) upsert(evt({ jobId: `job_${i}` }), i)
    const ids = Object.keys(useSocialProgressStore.getState().byJob)
    expect(ids.length).toBe(24)
    expect(ids).not.toContain('job_0') // oldest evicted
    expect(ids).toContain('job_29') // newest kept
  })

  it('clear() removes a single job', () => {
    const { upsert, clear } = useSocialProgressStore.getState()
    upsert(evt({ jobId: 'reel_1' }), 1)
    upsert(evt({ jobId: 'reel_2' }), 2)
    clear('reel_1')
    expect(Object.keys(useSocialProgressStore.getState().byJob)).toEqual(['reel_2'])
  })

  it('clearDraftJobs() drops only the project’s draft-phase jobs (keeps render + other projects)', () => {
    const { upsert, clearDraftJobs } = useSocialProgressStore.getState()
    upsert(evt({ jobId: 'p1_draft', projectId: 'p1', phase: 'draft' }), 1)
    upsert(evt({ jobId: 'p1_render', projectId: 'p1', phase: 'render', step: 'broll', total: 4 }), 2)
    upsert(evt({ jobId: 'p2_draft', projectId: 'p2', phase: 'draft' }), 3)
    clearDraftJobs('p1')
    const ids = Object.keys(useSocialProgressStore.getState().byJob).sort()
    expect(ids).toEqual(['p1_render', 'p2_draft']) // p1's draft gone; p1 render + p2 draft kept
  })
})
