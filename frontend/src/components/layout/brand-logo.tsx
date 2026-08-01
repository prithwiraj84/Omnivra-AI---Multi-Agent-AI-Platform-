import { OmnivraMark } from '@/components/brand/omnivra-mark'
import { cn } from '@/lib/utils'

export interface BrandLogoProps {
  /** Hide the wordmark, showing only the logo tile (collapsed sidebar). */
  collapsed?: boolean
}

/**
 * BrandLogo — the OMNIVRA lockup: the multi-agent nexus mark on a cyan→violet gradient tile,
 * plus the "OMNIVRA / AI Company OS · V2.0" wordmark. The wordmark collapses away on the
 * icon-rail layout, leaving only the glowing tile.
 */
export function BrandLogo({ collapsed = false }: BrandLogoProps) {
  return (
    <div className={cn('flex items-center gap-3', collapsed && 'justify-center')}>
      <div
        className={cn(
          'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl',
          'bg-gradient-to-br from-omnivra-cyan via-omnivra-indigo to-omnivra-purple',
          'shadow-[0_4px_18px_-4px_rgba(99,102,241,0.65)] ring-1 ring-white/10',
        )}
      >
        <OmnivraMark className="h-[22px] w-[22px] text-omnivra-bg-root" />
      </div>

      {!collapsed && (
        <div className="flex min-w-0 flex-col leading-none">
          <span className="truncate text-sm font-semibold tracking-wide text-white">
            OMNIVRA
          </span>
          <span className="section-label mt-1 truncate normal-case tracking-normal">
            AI Company OS · V2.0
          </span>
        </div>
      )}
    </div>
  )
}
