import { Check, Loader2, X } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { JobProgress } from '@/store/social-progress'

/**
 * GenerationProgress — a live checklist of the steps a reel/post goes through while it
 * generates (storyboard/voiceover, caption/image) or renders (Pexels b-roll, voiceover,
 * MoviePy assemble). Each row reflects the latest 'social_progress' frame for that step:
 * a spinner while running, a check when done, an X on error. Purely presentational; the
 * frames are accumulated in the social-progress store and fed in as `job`.
 */
export function GenerationProgress({ job, className }: { job: JobProgress; className?: string }) {
  return (
    <div
      className={cn('rounded-lg border border-white/[0.06] bg-white/[0.02] p-3', className)}
      role="status"
      aria-live="polite"
    >
      <ul className="flex flex-col gap-1.5">
        {job.steps.map((s) => (
          <li key={s.step} className="flex items-start gap-2 text-xs">
            <span className="mt-0.5 shrink-0" aria-hidden>
              {s.status === 'running' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-omnivra-cyan" />
              ) : s.status === 'error' ? (
                <X className="h-3.5 w-3.5 text-omnivra-red" />
              ) : (
                <Check className="h-3.5 w-3.5 text-omnivra-emerald" />
              )}
            </span>
            <span className="min-w-0 flex-1">
              {/* Status as text too (not icon/color alone) so screen readers + color-blind users get it. */}
              <span className="sr-only">{s.status === 'error' ? 'failed' : s.status === 'running' ? 'in progress' : 'done'}: </span>
              <span
                className={cn(
                  s.status === 'running' ? 'text-[#e4e4e7]' : s.status === 'error' ? 'text-omnivra-pink' : 'text-[#a1a1aa]',
                )}
              >
                {s.label}
              </span>
              {s.detail && <span className="ml-1 text-[10px] text-[#71717a]">· {s.detail}</span>}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
