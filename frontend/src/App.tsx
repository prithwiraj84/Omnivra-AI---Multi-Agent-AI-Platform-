import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/components/layout/app-layout'
import { AuthGate } from '@/components/auth/auth-gate'
import { useInitSupabaseAuth } from '@/hooks/useSupabaseAuth'
import { Landing } from '@/pages/Landing'
import { AuthCallback } from '@/pages/AuthCallback'
import { Dashboard } from '@/pages/Dashboard'
import { Workspace } from '@/pages/Workspace'
import { Documents } from '@/pages/Documents'
import { DocumentStudio } from '@/pages/DocumentStudio'
import { KnowledgeBase } from '@/pages/KnowledgeBase'
import { Memory } from '@/pages/Memory'
import { Settings } from '@/pages/Settings'
import { Login } from '@/pages/Login'
import { Projects } from '@/pages/Projects'
import { Tasks } from '@/pages/Tasks'
import { Social } from '@/pages/Social'
import { Agents } from '@/pages/Agents'
import { Workflows } from '@/pages/Workflows'
import { Approvals } from '@/pages/Approvals'
import { Logs } from '@/pages/Logs'
import { Integrations } from '@/pages/Integrations'
import { Billing } from '@/pages/Billing'
import { Department } from '@/pages/departments/Department'
import { SecurityCenter } from '@/pages/centers/SecurityCenter'
import { MarketingCenter } from '@/pages/centers/MarketingCenter'
import { DocumentationCenter } from '@/pages/centers/DocumentationCenter'

/**
 * Department slug → display title for the generic "/departments/*" roster routes.
 * Quality, marketing and documentation are rendered by their dedicated centers
 * (see below) and are intentionally absent from this list.
 */
const DEPARTMENT_ROUTES: { path: string; slug: string }[] = [
  { path: '/departments/executive', slug: 'executive' },
  { path: '/departments/architecture', slug: 'architecture' },
  { path: '/departments/engineering', slug: 'engineering' },
  { path: '/departments/system-ops', slug: 'system-ops' },
]

export default function App() {
  // Install the Supabase OAuth listener once for the whole app (no-op when unconfigured).
  useInitSupabaseAuth()

  return (
    <Routes>
      {/* Public routes — the marketing landing + sign-in live outside the protected AppLayout shell. */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />

      {/* Everything else is guarded by AuthGate (a no-op in open mode). The app's home is /dashboard. */}
      <Route
        element={
          <AuthGate>
            <AppLayout />
          </AuthGate>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />

        <Route path="/projects" element={<Projects />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/social" element={<Social />} />
        <Route path="/document-studio" element={<DocumentStudio />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/workspace" element={<Workspace />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/knowledge" element={<KnowledgeBase />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/integrations" element={<Integrations />} />
        <Route path="/billing" element={<Billing />} />
        <Route path="/settings" element={<Settings />} />

        <Route path="/departments/quality" element={<SecurityCenter />} />
        <Route path="/departments/marketing" element={<MarketingCenter />} />
        <Route path="/departments/documentation" element={<DocumentationCenter />} />

        {DEPARTMENT_ROUTES.map(({ path, slug }) => (
          <Route key={path} path={path} element={<Department slug={slug} />} />
        ))}

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}
