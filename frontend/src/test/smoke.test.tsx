import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '@/App'
import { AppProviders } from '@/providers/AppProviders'

afterEach(cleanup)

function renderApp(route = '/') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AppProviders>
        <App />
      </AppProviders>
    </MemoryRouter>,
  )
}

describe('App shell', () => {
  it('mounts the command-center shell without crashing', () => {
    renderApp('/dashboard')
    // Sidebar brand mark proves the layout chrome rendered.
    expect(screen.getAllByText(/OMNIVRA/i).length).toBeGreaterThan(0)
  })

  it('renders the marketing landing on / (public front page)', () => {
    renderApp('/')
    expect(screen.getByText(/Run an entire company/i)).toBeTruthy()
    // The landing sits OUTSIDE the app chrome — no topbar search.
    expect(screen.queryByPlaceholderText(/Search anything/i)).toBeNull()
  })

  it('renders the dashboard greeting on /dashboard', () => {
    renderApp('/dashboard')
    expect(screen.getByText(/Good morning, Omnivra/i)).toBeTruthy()
  })

  it('renders a placeholder for an unbuilt route', () => {
    renderApp('/logs')
    // Topbar search is part of the persistent chrome on every route.
    expect(screen.getByPlaceholderText(/Search anything/i)).toBeTruthy()
  })

  it('renders the settings status page on /settings', () => {
    // Open mode: AuthGate renders children (the config query is pending/fails in jsdom),
    // so /settings mounts inside the chrome and shows its status cards.
    renderApp('/settings')
    expect(screen.getAllByText(/System Health/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Authentication/i)).toBeTruthy()
    expect(screen.getByText(/Realtime Channel/i)).toBeTruthy()
  })

  it('renders the login page on /login outside the app shell', () => {
    // /login is public and outside AppLayout — the topbar chrome must NOT be present,
    // but the OMNIVRA brand + the Sign in action must render.
    renderApp('/login')
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeTruthy()
    expect(screen.getByLabelText(/Username/i)).toBeTruthy()
    expect(screen.queryByPlaceholderText(/Search anything/i)).toBeNull()
  })

  it('lets the auth gate render children in open mode (no redirect to /login)', () => {
    // The default (open) mode must not bounce to /login: the dashboard greeting renders.
    renderApp('/dashboard')
    expect(screen.getByText(/Good morning, Omnivra/i)).toBeTruthy()
  })

  it('renders the live indicator reflecting the realtime channel state', () => {
    renderApp('/dashboard')
    // The topbar LiveIndicator is part of the persistent chrome. Its accessible name
    // ("Realtime: <state>") proves the WebSocket hook is wired into the UI store —
    // the exact state depends on whether the test host exposes a WebSocket global.
    const indicators = screen.getAllByRole('status', { name: /Realtime:/i })
    expect(indicators.length).toBeGreaterThan(0)
  })

  it('renders the Phase-3 dashboard sections', () => {
    renderApp('/dashboard')
    for (const label of [
      /AI Agents Status/i,
      /Active Workflows/i,
      /Task Execution Overview/i,
      /Task Distribution/i,
      /Live Activity Feed/i,
      /Pending Approvals/i,
      /System Health/i,
      /Recent Achievements/i,
    ]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0)
    }
    // Live dashboard: the stat labels render (values are "—" until the backend responds),
    // and offline (jsdom) the empty panels show their empty states — no fake demo data.
    expect(screen.getAllByText(/Success Rate/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/No active workflows yet/i)).toBeTruthy()
  })

  it('renders the workspace artifact explorer on /workspace', () => {
    // Artifact queries fail offline (jsdom) — the explorer must still mount and
    // show its SectionHeader title (the empty/list state is data-dependent).
    renderApp('/workspace')
    expect(screen.getByText(/Workspace Artifacts/i)).toBeTruthy()
  })

  it('renders the knowledge base on /knowledge', () => {
    // Knowledge queries fail offline (jsdom) — the page must still mount and show
    // its SectionHeader title (the sidebar nav also labels it, hence getAllByText);
    // the search field + empty state are data-dependent.
    renderApp('/knowledge')
    expect(screen.getAllByText(/Knowledge Base/i).length).toBeGreaterThan(0)
    expect(screen.getByLabelText(/Search the knowledge base/i)).toBeTruthy()
  })

  it('renders the memory view on /memory', () => {
    // Memory queries fail offline (jsdom) — the page must still mount and render
    // its search control + empty state without crashing.
    renderApp('/memory')
    expect(screen.getByLabelText(/Search agent memory/i)).toBeTruthy()
  })

  it('renders the projects page on /projects', () => {
    // Project queries fail offline (jsdom) — the page must still mount and show its
    // SectionHeader (the sidebar nav also labels it, hence getAllByText), the create
    // form control, and the empty state.
    renderApp('/projects')
    expect(screen.getAllByText(/Projects/i).length).toBeGreaterThan(0)
    expect(screen.getByLabelText(/New project name/i)).toBeTruthy()
    expect(screen.getByRole('button', { name: /New Project/i })).toBeTruthy()
    expect(screen.getByText(/No projects yet/i)).toBeTruthy()
  })

  it('renders the tasks kanban board on /tasks', () => {
    // Task queries fail offline (jsdom) — the board must still mount and show all four
    // columns, the create row controls, and the per-column empty state.
    renderApp('/tasks')
    expect(screen.getByLabelText(/New task title/i)).toBeTruthy()
    expect(screen.getByLabelText(/Project for the new task/i)).toBeTruthy()
    expect(screen.getByRole('button', { name: /Add Task/i })).toBeTruthy()
    for (const column of [/To Do/i, /In Progress/i, /Review/i, /Done/i]) {
      expect(screen.getAllByText(column).length).toBeGreaterThan(0)
    }
    // Every column is empty offline, so the "No tasks" empty state appears 4×.
    expect(screen.getAllByText(/No tasks/i).length).toBe(4)
  })

  it('renders the Social Studio on /social', () => {
    // Social drafts fail offline (jsdom) — the studio must still mount and show its
    // composer (the sidebar nav also labels it, hence getAllByText) + empty state.
    renderApp('/social')
    expect(screen.getAllByText(/Social Studio/i).length).toBeGreaterThan(0)
    expect(screen.getByLabelText(/Content brief/i)).toBeTruthy()
    expect(screen.getByText(/No drafts yet/i)).toBeTruthy()
  })

  it('renders the Document Studio on /document-studio', () => {
    // Document drafts fail offline (jsdom) — the studio must still mount and show its
    // composer (the sidebar nav also labels it, hence getAllByText) + empty state.
    renderApp('/document-studio')
    expect(screen.getAllByText(/Document Studio/i).length).toBeGreaterThan(0)
    expect(screen.getByLabelText(/Document prompt/i)).toBeTruthy()
    expect(screen.getByText(/No documents yet/i)).toBeTruthy()
  })

  it('renders the run-task control in the greeting hero', () => {
    // RunTask dispatches a task to the CEO agent. Offline (jsdom), the run/awaiting
    // queries simply never resolve — the control must still render without crashing.
    renderApp('/dashboard')
    expect(screen.getByRole('button', { name: /Assign to CEO/i })).toBeTruthy()
    expect(screen.getByLabelText(/Task to assign to the CEO agent/i)).toBeTruthy()
  })

  // Every primary route must MOUNT without throwing, even offline (queries fail -> empty
  // states). The persistent topbar search proves the page rendered inside the chrome rather
  // than crashing. These cover the pages reported as "not working".
  it.each([
    ['/workflows'],
    ['/approvals'],
    ['/documents'],
    ['/departments/marketing'],
    ['/departments/system-ops'],
    ['/departments/quality'],
    ['/departments/documentation'],
    ['/departments/executive'],
    ['/integrations'],
    ['/billing'],
  ])('mounts %s without crashing', (route) => {
    renderApp(route)
    expect(screen.getByPlaceholderText(/Search anything/i)).toBeTruthy()
  })
})
