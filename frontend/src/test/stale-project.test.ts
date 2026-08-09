/**
 * Stale active-project self-healing (cp-0072).
 *
 * The active project id is persisted in localStorage, but the project behind it can vanish
 * server-side (ephemeral hosted disk, per-user mode hiding pre-login projects). Every request
 * then carries a dead X-Project-Id and 404s — the reported symptom was "Assign to CEO →
 * Could not reach the company". These pin the decision function the healer runs on.
 */
import { describe, expect, it } from 'vitest'
import { isStaleProject } from '@/hooks/useProjects'
import { DEFAULT_PROJECT_ID } from '@/store/project'
import type { Project } from '@/lib/api/types'

function project(id: string): Project {
  return { id, name: id, createdAt: '', taskCount: 0 } as unknown as Project
}

describe('isStaleProject', () => {
  it('flags an active id the server no longer knows', () => {
    expect(isStaleProject('proj_gone', [project('proj_a'), project('proj_b')])).toBe(true)
    expect(isStaleProject('proj_gone', [])).toBe(true)
  })

  it('keeps an active id that still exists', () => {
    expect(isStaleProject('proj_a', [project('proj_a')])).toBe(false)
  })

  it('never treats the default workspace as stale', () => {
    // The backend maps the default id to THIS user's Default Workspace on every request —
    // it always resolves, even when the list shows a per-user id instead.
    expect(isStaleProject(DEFAULT_PROJECT_ID, [])).toBe(false)
    expect(isStaleProject(DEFAULT_PROJECT_ID, [project('user_default_123')])).toBe(false)
  })
})
