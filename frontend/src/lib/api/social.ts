/**
 * Social content pipeline API calls (cp-0017). Uses the shared `@/lib/api/client`
 * axios instance (baseURL '/api'); the active project rides on the X-Project-Id
 * header set by the interceptor, so these are implicitly project-scoped.
 */
import { api } from '@/lib/api/client'
import type { PostRequest, ReelRequest, SocialDecision, SocialDraft } from '@/lib/api/types'

/** Draft a short-form reel (storyboard + stub voiceover). POST /social/reel. */
export async function draftReel(body: ReelRequest): Promise<SocialDraft> {
  const { data } = await api.post<SocialDraft>('/social/reel', body)
  return data
}

/** Draft an image post (FLUX image + caption + tags). POST /social/post. */
export async function draftPost(body: PostRequest): Promise<SocialDraft> {
  const { data } = await api.post<SocialDraft>('/social/post', body)
  return data
}

/** The active project's social drafts (newest first). GET /social/drafts. */
export async function listDrafts(): Promise<SocialDraft[]> {
  const { data } = await api.get<SocialDraft[]>('/social/drafts')
  return data
}

/** Approve (-> publish) or reject a draft. POST /social/drafts/{id}/decision. */
export async function decideDraft(id: string, body: SocialDecision): Promise<SocialDraft> {
  const { data } = await api.post<SocialDraft>(`/social/drafts/${id}/decision`, body)
  return data
}

/** Kick off an async render of a reel draft into an .mp4. POST /social/drafts/{id}/render. */
export async function renderDraft(id: string): Promise<SocialDraft> {
  const { data } = await api.post<SocialDraft>(`/social/drafts/${id}/render`, {})
  return data
}

/** Hard-delete a draft and all of its artifacts. DELETE /social/drafts/{id}. */
export async function deleteDraft(id: string): Promise<void> {
  await api.delete(`/social/drafts/${id}`)
}

/**
 * Direct URL for a workspace media artifact (rendered .mp4 / generated image), for a
 * native <video>/<img> src. Carries projectId as a query param because those elements
 * don't send the X-Project-Id header the axios interceptor adds.
 */
export function mediaUrl(path: string, projectId: string): string {
  const clean = path.split('/').map(encodeURIComponent).join('/')
  return `/api/workspace/media/${clean}?projectId=${encodeURIComponent(projectId)}`
}
