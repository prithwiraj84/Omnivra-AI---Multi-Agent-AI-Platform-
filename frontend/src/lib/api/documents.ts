/**
 * Document Studio API calls (cp-0025). Uses the shared `@/lib/api/client` axios
 * instance (baseURL '/api'); the active project rides on the X-Project-Id header
 * set by the interceptor, so these are implicitly project-scoped.
 */
import { api, apiUrl } from '@/lib/api/client'
import type { DocumentDecision, DocumentDraft, DocumentRequest } from '@/lib/api/types'

/** Generate a document from a prompt in the chosen format. POST /documents/generate. */
export async function generateDocument(body: DocumentRequest): Promise<DocumentDraft> {
  const { data } = await api.post<DocumentDraft>('/documents/generate', body)
  return data
}

/** The active project's document drafts (newest first). GET /documents. */
export async function listDocuments(): Promise<DocumentDraft[]> {
  const { data } = await api.get<DocumentDraft[]>('/documents')
  return data
}

/** Approve or reject a drafted document. POST /documents/{id}/decision. */
export async function decideDocument(id: string, body: DocumentDecision): Promise<DocumentDraft> {
  const { data } = await api.post<DocumentDraft>(`/documents/${id}/decision`, body)
  return data
}

/**
 * Direct URL for a workspace document artifact (the rendered .pptx/.docx/.pdf or the
 * markdown deliverable), for a download link. Carries projectId as a query param
 * because an <a href> doesn't send the X-Project-Id header the axios interceptor adds.
 */
export function documentUrl(path: string, projectId: string): string {
  const clean = path.split('/').map(encodeURIComponent).join('/')
  return apiUrl(`/workspace/media/${clean}?projectId=${encodeURIComponent(projectId)}`)
}
