/**
 * LiveIndicator — a compact topbar pill reflecting the live /ws connection state
 * (useUIStore.realtimeStatus, driven by hooks/useWebSocket). A StatusDot + label:
 *   - open                    -> emerald pulsing dot, "Live"
 *   - connecting / idle        -> amber dot, "Connecting"
 *   - closed / unsupported     -> idle (zinc) dot, "Offline"
 */
import { StatusDot } from '@/components/ui/status-dot'
import { useUIStore } from '@/store/ui'
import { cn } from '@/lib/utils'

type Visual = {
  dot: 'online' | 'busy' | 'idle'
  pulse: boolean
  label: string
  text: string
}

export function LiveIndicator({ className }: { className?: string }) {
  const status = useUIStore((s) => s.realtimeStatus)

  let v: Visual
  if (status === 'open') {
    v = { dot: 'online', pulse: true, label: 'Live', text: 'text-omnivra-emerald-bright' }
  } else if (status === 'connecting' || status === 'idle') {
    v = { dot: 'busy', pulse: false, label: 'Connecting', text: 'text-omnivra-amber' }
  } else {
    // 'closed' | 'unsupported'
    v = { dot: 'idle', pulse: false, label: 'Offline', text: 'text-zinc-400' }
  }

  return (
    <span
      className={cn('inline-flex items-center gap-1.5', className)}
      role="status"
      aria-label={`Realtime: ${v.label}`}
    >
      <StatusDot status={v.dot} pulse={v.pulse} aria-hidden />
      <span className={cn('hidden text-[11px] font-medium sm:inline', v.text)}>{v.label}</span>
    </span>
  )
}
