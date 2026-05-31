import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/components/layout/app-layout'
import { AuthGate } from '@/components/auth/auth-gate'
import { Dashboard } from '@/pages/Dashboard'
import { Workspace } from '@/pages/Workspace'
import { Documents } from '@/pages/Documents'
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
  return (
    <Routes>
      {/* Public route — sign-in lives outside the protected AppLayout shell. */}
      <Route path="/login" element={<Login />} />

      {/* Everything else is guarded by AuthGate (a no-op in open mode). */}
      <Route
        element={
          <AuthGate>
            <AppLayout />
          </AuthGate>
        }
      >
        <Route index element={<Dashboard />} />

        <Route path="/projects" element={<Projects />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/social" element={<Social />} />
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

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
