import { forwardRef } from 'react'
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu'
import { cn } from '@/lib/utils'

/**
 * DropdownMenu — Radix dropdown with a glass-strong content surface and
 * popover shadow, consistent with the rest of the Omnivra menu surfaces.
 */
const DropdownMenu = DropdownMenuPrimitive.Root

const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger

const DropdownMenuContent = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 6, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        'glass-strong z-50 min-w-[12rem] overflow-hidden rounded-lg p-1.5 text-sm text-foreground ' +
          'shadow-popover animate-fade-up ' +
          'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 ' +
          'data-[side=bottom]:slide-in-from-top-1 data-[side=left]:slide-in-from-right-1 ' +
          'data-[side=right]:slide-in-from-left-1 data-[side=top]:slide-in-from-bottom-1',
        className,
      )}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
))
DropdownMenuContent.displayName = DropdownMenuPrimitive.Content.displayName

const DropdownMenuItem = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item> & { inset?: boolean }
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      'relative flex cursor-pointer select-none items-center gap-2 rounded-md px-2.5 py-2 text-sm ' +
        'text-foreground/80 outline-none transition-colors ' +
        'focus:bg-white/5 focus:text-foreground data-[highlighted]:bg-white/5 data-[highlighted]:text-foreground ' +
        'data-[disabled]:pointer-events-none data-[disabled]:opacity-50 ' +
        '[&_svg]:size-4 [&_svg]:shrink-0 [&_svg]:text-muted-foreground',
      inset && 'pl-8',
      className,
    )}
    {...props}
  />
))
DropdownMenuItem.displayName = DropdownMenuPrimitive.Item.displayName

const DropdownMenuLabel = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Label> & { inset?: boolean }
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Label
    ref={ref}
    className={cn('px-2.5 py-1.5 section-label', inset && 'pl-8', className)}
    {...props}
  />
))
DropdownMenuLabel.displayName = DropdownMenuPrimitive.Label.displayName

const DropdownMenuSeparator = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Separator
    ref={ref}
    className={cn('-mx-1 my-1 h-px bg-border', className)}
    {...props}
  />
))
DropdownMenuSeparator.displayName = DropdownMenuPrimitive.Separator.displayName

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
}
