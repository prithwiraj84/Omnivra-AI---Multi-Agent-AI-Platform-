/**
 * Document Studio hooks (cp-0025).
 *  - useDocuments(): the active project's document drafts, polled every 10s.
 *  - useGenerateDocument(): generate a document, then refresh the list.
 *  - useDecideDocument(): approve or reject a draft, then refresh.
 * All scoped to the active project (query key carries it; the X-Project-Id header
 * does the server-side scoping). Fail gracefully offline (jsdom/tests) -> [].
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { decideDocument, generateDocument, listDocuments } from '@/lib/api/documents'
import type { DocumentDecision, DocumentDraft, DocumentRequest } from '@/lib/api/types'
import { useProjectStore } from '@/store/project'

/** Live document drafts for the active project — polled; one retry so offline settles fast. */
export function useDocuments() {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<DocumentDraft[]>({
    queryKey: ['documents', projectId],
    queryFn: listDocuments,
    refetchInterval: 10_000,
    retry: 1,
  })
}

/** Generate a document; refreshes the drafts list on success. */
export function useGenerateDocument() {
  const qc = useQueryClient()
  return useMutation<DocumentDraft, Error, DocumentRequest>({
    mutationFn: generateDocument,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  })
}

interface DecisionVars {
  id: string
  decision: DocumentDecision
}

/** Approve/reject a document; refreshes the drafts list on success. */
export function useDecideDocument() {
  const qc = useQueryClient()
  return useMutation<DocumentDraft, Error, DecisionVars>({
    mutationFn: ({ id, decision }) => decideDocument(id, decision),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  })
}
