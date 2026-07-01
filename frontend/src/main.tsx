import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import App from '@/App'
import { AppProviders } from '@/providers/AppProviders'
import { ErrorBoundary } from '@/components/common/error-boundary'
import '@/index.css'

const rootEl = document.getElementById('root')
if (!rootEl) throw new Error('Root element #root not found')

createRoot(rootEl).render(
  <StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      {/* reducedMotion="user" makes framer-motion strip transform/layout animations (keeping opacity)
          for visitors who prefer reduced motion — across every initial/animate/whileInView in the app. */}
      <MotionConfig reducedMotion="user">
        <AppProviders>
          <ErrorBoundary>
            <App />
          </ErrorBoundary>
        </AppProviders>
      </MotionConfig>
    </BrowserRouter>
  </StrictMode>,
)
