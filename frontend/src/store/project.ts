/**
 * Active-project state (Zustand). Holds the project the UI is currently scoped to.
 * Persisted to localStorage under `omnivra.activeProjectId` (same manual pattern as
 * the auth store) so it survives reloads and the axios request interceptor (see
 * lib/api/client) can read it to set the `X-Project-Id` header on every request.
 *
 * Every project owns an isolated workspace on the backend (artifacts, RAG memory,
 * knowledge base, workflow runs). The Default Workspace (`__default__`) always
 * exists and is never deletable.
 */
import { create } from 'zustand'

/** The always-present default project (matches the backend DEFAULT_PROJECT). */
export const DEFAULT_PROJECT_ID = '__default__'
/** localStorage key the active project is persisted under (shared with the interceptor). */
export const PROJECT_STORAGE_KEY = 'omnivra.activeProjectId'

/** Read the persisted active project, tolerating environments without localStorage. */
function readStored(): string {
  try {
    return localStorage.getItem(PROJECT_STORAGE_KEY) || DEFAULT_PROJECT_ID
  } catch {
    return DEFAULT_PROJECT_ID
  }
}

function writeStored(id: string): void {
  try {
    localStorage.setItem(PROJECT_STORAGE_KEY, id)
  } catch {
    /* no-op: localStorage unavailable (private mode / jsdom) */
  }
}

interface ProjectState {
  /** The project the UI is scoped to (sent as X-Project-Id on every request). */
  activeProjectId: string
  /** Switch the active project (persists + updates the store). */
  setActiveProject: (id: string) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  activeProjectId: readStored(),
  setActiveProject: (id) => {
    const next = id || DEFAULT_PROJECT_ID
    writeStored(next)
    set({ activeProjectId: next })
  },
}))

/**
 * Plain getter for non-React modules (the axios interceptor). Reads the live store
 * value so every request carries the current project. Falls back to the default.
 */
export function getActiveProjectId(): string {
  try {
    return useProjectStore.getState().activeProjectId || DEFAULT_PROJECT_ID
  } catch {
    return DEFAULT_PROJECT_ID
  }
}
