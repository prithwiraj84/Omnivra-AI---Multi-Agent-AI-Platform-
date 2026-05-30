import { type PropsWithChildren, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TooltipProvider } from '@/components/ui/tooltip'

export function AppProviders({ children }: PropsWithChildren) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 30000, retry: 2, refetchOnWindowFocus: false } },
      }),
  )
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider delayDuration={200} skipDelayDuration={300}>
        {children}
      </TooltipProvider>
    </QueryClientProvider>
  )
}
