/** The Error Log's copy format (cp-0073) — what lands in a bug report must be complete. */
import { describe, expect, it } from 'vitest'
import { formatErrorForCopy } from '@/pages/ErrorLog'
import type { ErrorItem } from '@/lib/api/errorLog'

function item(p: Partial<ErrorItem>): ErrorItem {
  return {
    id: 1, ts: '2026-08-09T10:00:00Z', lastTs: '2026-08-09T10:05:00Z',
    level: 'warning', category: 'media', source: 'app.services.media:generate_image:84',
    message: 'Image generation failed', detail: '', count: 1, ...p,
  }
}

describe('formatErrorForCopy', () => {
  it('carries level, category, message, source and time', () => {
    const text = formatErrorForCopy(item({}))
    expect(text).toContain('[WARNING] Media / Voice')
    expect(text).toContain('Image generation failed')
    expect(text).toContain('source: app.services.media:generate_image:84')
    expect(text).toContain('time: 2026-08-09T10:05:00Z')
  })

  it('includes the repeat count and the exception detail when present', () => {
    const text = formatErrorForCopy(item({ count: 4, detail: "FatalProviderError('410: deprecated')" }))
    expect(text).toContain('(x4)')
    expect(text).toContain("detail: FatalProviderError('410: deprecated')")
  })

  it('degrades gracefully for a category the UI does not know yet', () => {
    expect(formatErrorForCopy(item({ category: 'future_thing' }))).toContain('[WARNING] future_thing')
  })
})
