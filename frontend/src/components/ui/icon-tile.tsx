import { forwardRef } from 'react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { accentClasses } from '@/lib/accents'
import type { Accent } from '@/types'

/**
 * IconTile — the tinted rounded square that fronts stat cards, agent cards and
 * list rows. The accent tint (background + icon color) comes from `.tile-*`.
 */
export interface IconTileProps extends React.HTMLAttributes<HTMLDivElement> {
  accent: Accent
  size?: 'sm' | 'md'
  icon: LucideIcon
}

const sizeBox: Record<NonNullable<IconTileProps['size']>, string> = {
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
}

const sizeIcon: Record<NonNullable<IconTileProps['size']>, string> = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
}

export const IconTile = forwardRef<HTMLDivElement, IconTileProps>(
  ({ accent, size = 'md', icon: Icon, className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex shrink-0 items-center justify-center rounded-md',
        sizeBox[size],
        accentClasses(accent).tile,
        className,
      )}
      {...props}
    >
      <Icon className={sizeIcon[size]} strokeWidth={2} aria-hidden />
    </div>
  ),
)
IconTile.displayName = 'IconTile'
