import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle, RotateCcw } from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { Button } from '@/components/ui/button'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

/**
 * ErrorBoundary — catches render-time errors anywhere below it and shows an on-brand
 * fallback (a centered GlassCard with "Something went wrong" + a Reload button) instead
 * of a blank white screen. Wraps the whole app (see main.tsx). Recovery is a full page
 * reload so React Query / WebSocket / store state all reset cleanly.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Surface the error for debugging; in production this is where telemetry would go.
    console.error('Unhandled render error:', error, info)
  }

  private handleReload = (): void => {
    window.location.reload()
  }

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children
    }

    return (
      <div
        className="relative flex min-h-screen w-full items-center justify-center overflow-hidden p-6"
        style={{ backgroundColor: 'var(--omni-bg-base)' }}
      >
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 bg-grid-faint [background-size:32px_32px] opacity-60"
        />
        <div
          aria-hidden
          className="ambient-glow pointer-events-none fixed inset-x-0 top-0 h-[420px]"
        />

        <GlassCard variant="strong" padding="lg" className="relative z-10 w-full max-w-sm">
          <div className="flex flex-col items-center gap-5 text-center" role="alert">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/[0.04] text-omnivra-pink ring-1 ring-white/[0.06]">
              <AlertTriangle className="h-6 w-6" aria-hidden />
            </div>
            <div className="flex flex-col gap-1.5">
              <h1 className="text-base font-semibold text-white">Something went wrong</h1>
              <p className="max-w-[34ch] text-xs leading-relaxed text-[#71717a]">
                An unexpected error interrupted the interface. Reloading should restore the
                command center.
              </p>
            </div>
            <Button type="button" onClick={this.handleReload}>
              <RotateCcw aria-hidden />
              Reload
            </Button>
          </div>
        </GlassCard>
      </div>
    )
  }
}
