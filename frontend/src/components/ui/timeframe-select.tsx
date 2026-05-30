import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export interface TimeframeSelectProps {
  /** Currently selected option. */
  value: string
  /** Selectable options (e.g. `['Daily', 'Weekly', 'Monthly']`). */
  options: string[]
  /** Called with the chosen option. */
  onChange?: (value: string) => void
  /** Extra classes for the trigger button. */
  className?: string
}

/**
 * TimeframeSelect — a compact dropdown showing the current value + chevron,
 * used by chart headers (e.g. the "Daily" selector). Built on the shadcn
 * dropdown-menu primitive.
 */
export function TimeframeSelect({ value, options, onChange, className }: TimeframeSelectProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className={cn(
            'focus-ring inline-flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-omnivra-surface-2 px-3 py-1.5 text-xs font-medium text-[#e4e4e7] transition-colors duration-200 ease-out-quint hover:border-white/[0.12] hover:text-white',
            className,
          )}
        >
          <span className="tabular">{value}</span>
          <ChevronDown className="h-3.5 w-3.5 text-[#71717a]" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[8rem]">
        {options.map((option) => (
          <DropdownMenuItem
            key={option}
            onSelect={() => onChange?.(option)}
            className={cn('text-xs', option === value && 'text-omnivra-cyan')}
          >
            {option}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
