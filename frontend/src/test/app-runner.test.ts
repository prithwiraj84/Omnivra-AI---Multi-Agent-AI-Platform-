/**
 * App runner "open in a new tab" targeting (cp-0069).
 *
 * Clicking Run opens a tab synchronously (a user gesture — window.open from the later async
 * status poll would be popup-blocked) and redirects it once a target is serving. These cover
 * the two decisions that tab depends on: WHICH target it lands on, and WHEN to give up.
 */
import { describe, expect, it } from 'vitest'
import { openableTarget, runSettled } from '@/components/workspace/app-runner-panel'
import type { AppTarget } from '@/lib/api/types'

function target(p: Partial<AppTarget>): AppTarget {
  return {
    runKey: p.runKey ?? 'k',
    rel: p.rel ?? 'app',
    kind: p.kind ?? 'python',
    name: p.name ?? 'app',
    framework: p.framework ?? '',
    status: p.status ?? 'idle',
    port: p.port ?? null,
    url: p.url ?? null,
    exitCode: p.exitCode ?? null,
    note: p.note ?? '',
    logsTail: p.logsTail ?? '',
  }
}

describe('openableTarget', () => {
  it('prefers the frontend — "run the app" means the website, not its API root', () => {
    const targets = [
      target({ runKey: 'api', kind: 'python', status: 'running', url: 'http://127.0.0.1:8001' }),
      target({ runKey: 'web', kind: 'node', status: 'running', url: 'http://127.0.0.1:5174' }),
    ]
    expect(openableTarget(targets)?.runKey).toBe('web')
  })

  it('falls back to the backend when the app has no frontend', () => {
    const targets = [target({ runKey: 'api', kind: 'python', status: 'running', url: 'http://127.0.0.1:8001' })]
    expect(openableTarget(targets)?.runKey).toBe('api')
  })

  it('ignores targets that are not serving yet', () => {
    const targets = [
      target({ kind: 'node', status: 'installing' }),
      target({ kind: 'python', status: 'starting' }),
    ]
    expect(openableTarget(targets)).toBeUndefined()
  })

  it('ignores a running target with no url — there is nowhere to send the tab', () => {
    expect(openableTarget([target({ kind: 'node', status: 'running', url: null })])).toBeUndefined()
  })

  it('does not pick the frontend until IT is running', () => {
    const targets = [
      target({ runKey: 'api', kind: 'python', status: 'running', url: 'http://127.0.0.1:8001' }),
      target({ runKey: 'web', kind: 'node', status: 'installing' }),
    ]
    // The backend is up first; the tab should not sit empty waiting for the frontend.
    expect(openableTarget(targets)?.runKey).toBe('api')
  })
})

describe('runSettled', () => {
  it('is false while anything is still working', () => {
    expect(runSettled([target({ status: 'installing' }), target({ status: 'error' })])).toBe(false)
    expect(runSettled([target({ status: 'starting' })])).toBe(false)
    expect(runSettled([target({ status: 'running' })])).toBe(false)
  })

  it('is true only once every target has stopped for good', () => {
    expect(runSettled([target({ status: 'error' }), target({ status: 'exited' })])).toBe(true)
    expect(runSettled([target({ status: 'stopped' })])).toBe(true)
  })

  it('treats idle as NOT settled — it is also the state before the run request is answered', () => {
    // Abandoning the tab on 'idle' would kill it milliseconds after the click, every time.
    expect(runSettled([target({ status: 'idle' })])).toBe(false)
    expect(runSettled([])).toBe(false)
  })
})

describe('appPreviewUrl', () => {
  it('carries the project in the PATH so relative asset URLs keep it', async () => {
    const { appPreviewUrl } = await import('@/lib/api/appRunner')
    const url = appPreviewUrl('docs/wf_x/site/index.html', 'proj_1')
    // The page's assets resolve against this URL — a ?projectId= would be dropped by the browser.
    expect(url).toContain('/workspace/app/preview/proj_1/docs/wf_x/site/index.html')
    expect(url).not.toContain('projectId=')
  })

  it('percent-encodes each path segment without eating the separators', async () => {
    const { appPreviewUrl } = await import('@/lib/api/appRunner')
    const url = appPreviewUrl('docs/wf x/a b.html', 'p 1')
    expect(url).toContain('/workspace/app/preview/p%201/docs/wf%20x/a%20b.html')
  })
})
