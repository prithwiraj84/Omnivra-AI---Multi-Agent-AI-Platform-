import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

/**
 * KbdHint — a row of monospace key chips (e.g. ⌘ K) for the command palette
 * trigger and shortcut affordances.
 */
export interface KbdHintProps extends React.HTMLAttributes<HTMLSpanElement> {
  keys: string[]
}

export const KbdHint = forwardRef<HTMLSpanElement, KbdHintProps>(
  ({ keys, className, ...props }, ref) => (
    <span ref={ref} className={cn('inline-flex items-center gap-1', className)} {...props}>
      {keys.map((key, i) => (
        <kbd
          key={`${key}-${i}`}
          className="inline-flex h-5 min-w-5 items-center justify-center rounded-md border border-white/10 bg-omnivra-surface-2 px-1.5 font-mono text-[10px] font-medium leading-none text-zinc-400 shadow-[inset_0_-1px_0_0_rgba(0,0,0,0.4)]"
        >
          {key}
        </kbd>
      ))}
    </span>
  ),
)
KbdHint.displayName = 'KbdHint'
