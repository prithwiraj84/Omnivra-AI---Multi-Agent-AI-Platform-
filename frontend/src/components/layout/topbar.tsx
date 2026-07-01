import { useNavigate } from 'react-router-dom'

import { LiveIndicator } from '@/components/dashboard/live-indicator'
import { ProjectSwitcher } from '@/components/layout/project-switcher'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { IconButton } from '@/components/ui/icon-button'
import { KbdHint } from '@/components/ui/kbd-hint'
import { useSupabaseAuth } from '@/hooks/useSupabaseAuth'
import { avatarUrl, displayName, initials } from '@/lib/user-profile'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/auth'
import { useUIStore } from '@/store/ui'
import { Bell, LogOut, Menu, Search, Settings, User } from 'lucide-react'

export interface TopbarProps extends React.HTMLAttributes<HTMLElement> {
  /** Notification count rendered on the bell badge. */
  notifications?: number
  /** Optional handler for the search input. */
  onSearch?: (value: string) => void
}

/**
 * Topbar — the fixed 60px global top bar. Left: a sidebar collapse toggle.
 * Center-left (grows): a "Search anything…" field with a ⌘K hint. Right: bell
 * (with count badge), settings, and an avatar dropdown (Profile / Settings /
 * Sign out) labelled "Omnivra / Super Admin".
 */
export function Topbar({ notifications = 12, onSearch, className, ...props }: TopbarProps) {
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const navigate = useNavigate()
  const { user, isAuthenticated, signOut } = useSupabaseAuth()
  const clearAuth = useAuthStore((s) => s.clearAuth)

  // Signed-in identity (Google/GitHub) drives the avatar + account menu; falls back to the
  // single-admin label in open mode.
  const name = isAuthenticated ? displayName(user) : 'Omnivra'
  const subtitle = isAuthenticated ? user?.email ?? 'Signed in' : 'Super Admin'
  const photo = avatarUrl(user)

  async function handleSignOut() {
    await signOut() // clears the Supabase session (no-op when unconfigured)
    clearAuth() // clears the backend bearer token too
    navigate('/', { replace: true })
  }

  return (
    <header
      className={cn(
        'flex h-[60px] shrink-0 items-center gap-3 border-b border-white/[0.08] px-4',
        className,
      )}
      style={{ backgroundColor: 'var(--omni-bg-topbar)' }}
      {...props}
    >
      {/* Left: sidebar collapse + active-project switcher */}
      <IconButton icon={Menu} aria-label="Toggle sidebar" onClick={toggleSidebar} />
      <ProjectSwitcher className="hidden sm:flex" />

      {/* Center-left: search (grows to fill) */}
      <div className="relative flex max-w-md flex-1 items-center">
        <Search
          className="pointer-events-none absolute left-3 h-[18px] w-[18px] text-[#71717a]"
          aria-hidden
        />
        <input
          type="text"
          placeholder="Search anything..."
          aria-label="Search anything"
          onChange={(e) => onSearch?.(e.target.value)}
          className="focus-ring h-9 w-full rounded-md bg-omnivra-surface-2 pl-10 pr-16 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
        />
        <KbdHint keys={['⌘', 'K']} className="pointer-events-none absolute right-2.5" />
      </div>

      {/* Right cluster */}
      <div className="ml-auto flex items-center gap-1.5">
        <LiveIndicator className="mr-1.5" />
        <IconButton icon={Bell} aria-label="Notifications" badge={notifications} />
        <IconButton icon={Settings} aria-label="Settings" onClick={() => navigate('/settings')} />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label="Account menu"
              className="focus-ring ml-1 rounded-full"
            >
              <Avatar className="h-9 w-9">
                {photo && <AvatarImage src={photo} alt={name} />}
                <AvatarFallback className="bg-omnivra-surface-3 text-omnivra-cyan">
                  {isAuthenticated ? initials(name) : 'OM'}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="min-w-[14rem]">
            <DropdownMenuLabel>
              <span className="block truncate text-sm font-semibold normal-case tracking-normal text-[#fafafa]">
                {name}
              </span>
              <span className="block truncate text-xs font-normal normal-case tracking-normal text-[#a1a1aa]">
                {subtitle}
              </span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate('/profile')}>
              <User />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate('/settings')}>
              <Settings />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleSignOut}
              className="text-omnivra-red/90 focus:text-omnivra-red data-[highlighted]:text-omnivra-red [&_svg]:text-omnivra-red/80"
            >
              <LogOut />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
