/**
 * CountUp regression tests — guards the dashboard "everything reads 0" bug, where the animation
 * effect depended on the per-render `match` array and reset the counter to 0 on every re-render.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, cleanup } from '@testing-library/react'

import { CountUp } from '@/components/common/count-up'

describe('CountUp', () => {
  beforeEach(() => {
    // Drive the rAF loop to completion in one frame so we can assert the settled value.
    let now = 0
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
      now += 10_000
      cb(now)
      return 1
    })
    vi.stubGlobal('cancelAnimationFrame', () => {})
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it('reaches the numeric target (not stuck at 0)', () => {
    const { container } = render(<CountUp value="23" />)
    expect(container.textContent).toBe('23')
  })

  it('renders prefix/suffix + decimals (e.g. percentages)', () => {
    expect(render(<CountUp value="100.0%" />).container.textContent).toBe('100.0%')
  })

  it('does NOT reset to 0 when re-rendered with the same value (poll/parent re-render)', () => {
    const { container, rerender } = render(<CountUp value="39" />)
    expect(container.textContent).toBe('39')
    rerender(<CountUp value="39" />)
    expect(container.textContent).toBe('39')
  })

  it('falls back to the literal string for non-numeric values', () => {
    expect(render(<CountUp value="—" />).container.textContent).toBe('—')
  })
})
