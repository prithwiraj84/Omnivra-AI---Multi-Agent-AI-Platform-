/**
 * Social pipeline hooks (cp-0017).
 *  - useSocialDrafts(): the active project's drafts, polled every 10s.
 *  - useDraftReel() / useDraftPost(): generate a draft, then refresh the list.
 *  - useDecideDraft(): approve (-> publish) or reject a draft, then refresh.
 * All scoped to the active project (query key carries it; the X-Project-Id header
 * does the server-side scoping). Fail gracefully offline (jsdom/tests) -> [].
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { decideDraft, draftPost, draftReel, listDrafts, renderDraft } from '@/lib/api/social'
import type { PostRequest, ReelRequest, SocialDecision, SocialDraft } from '@/lib/api/types'
import { useProjectStore } from '@/store/project'

/** Live social drafts for the active project — polled; one retry so offline settles fast. */
export function useSocialDrafts() {
  const projectId = useProjectStore((s) => s.activeProjectId)
  return useQuery<SocialDraft[]>({
    queryKey: ['social', 'drafts', projectId],
    queryFn: listDrafts,
    refetchInterval: 10_000,
    retry: 1,
  })
}

/** Draft a reel; refreshes the drafts list on success. */
export function useDraftReel() {
  const qc = useQueryClient()
  return useMutation<SocialDraft, Error, ReelRequest>({
    mutationFn: draftReel,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['social'] }),
  })
}

/** Draft a post; refreshes the drafts list on success. */
export function useDraftPost() {
  const qc = useQueryClient()
  return useMutation<SocialDraft, Error, PostRequest>({
    mutationFn: draftPost,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['social'] }),
  })
}

interface DecisionVars {
  id: string
  decision: SocialDecision
}

/** Approve/reject a draft; refreshes the drafts list on success. */
export function useDecideDraft() {
  const qc = useQueryClient()
  return useMutation<SocialDraft, Error, DecisionVars>({
    mutationFn: ({ id, decision }) => decideDraft(id, decision),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['social'] }),
  })
}

/** Kick off a reel render; refreshes the drafts list (status -> rendering, then polled). */
export function useRenderDraft() {
  const qc = useQueryClient()
  return useMutation<SocialDraft, Error, string>({
    mutationFn: (id) => renderDraft(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['social'] }),
  })
}
