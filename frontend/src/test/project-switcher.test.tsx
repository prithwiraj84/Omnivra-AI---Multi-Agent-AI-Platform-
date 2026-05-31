import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProjectSwitcher } from '@/components/layout/project-switcher'
import { DEFAULT_PROJECT_ID, useProjectStore } from '@/store/project'
import type { Project } from '@/lib/api/types'

afterEach(() => {
  cleanup()
  // Reset the active project so tests don't leak state into one another.
  useProjectStore.setState({ activeProjectId: DEFAULT_PROJECT_ID })
})

function renderSwitcher(seed?: Project[]) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  if (seed) qc.setQueryData(['projects'], seed)
  return render(
    <QueryClientProvider client={qc}>
      <ProjectSwitcher />
    </QueryClientProvider>,
  )
}

const project = (id: string, name: string, taskCount = 0): Project => ({
  id,
  name,
  description: '',
  status: 'active',
  createdAt: '2026-01-01',
  taskCount,
})

describe('ProjectSwitcher', () => {
  it('renders the Default Workspace label offline (no projects, no localStorage)', () => {
    useProjectStore.setState({ activeProjectId: DEFAULT_PROJECT_ID })
    renderSwitcher()
    expect(screen.getByRole('button', { name: /Switch project/i })).toBeTruthy()
    expect(screen.getByText(/Default Workspace/i)).toBeTruthy()
  })

  it('shows the active project name when one is selected', () => {
    useProjectStore.setState({ activeProjectId: 'proj-x' })
    renderSwitcher([project('__default__', 'Default Workspace'), project('proj-x', 'Marketing Q3', 2)])
    expect(screen.getByText(/Marketing Q3/i)).toBeTruthy()
  })
})
