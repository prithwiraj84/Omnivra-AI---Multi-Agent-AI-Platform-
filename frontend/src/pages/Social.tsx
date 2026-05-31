import { useState, type FormEvent } from 'react'
import {
  Check,
  Clapperboard,
  Film,
  Hash,
  Image as ImageIcon,
  Loader2,
  Megaphone,
  Wand2,
  X,
} from 'lucide-react'

import { GlassCard } from '@/components/ui/glass-card'
import { SectionHeader } from '@/components/ui/section-header'
import { NeonBadge, type BadgeTone } from '@/components/ui/neon-badge'
import { Chip } from '@/components/ui/chip'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import { cn } from '@/lib/utils'
import { useDecideDraft, useDraftPost, useDraftReel, useRenderDraft, useSocialDrafts } from '@/hooks/useSocial'
import { mediaUrl } from '@/lib/api/social'
import { useProjectStore } from '@/store/project'
import type { SocialDraft, SocialKind } from '@/lib/api/types'

const REEL_TARGETS = ['youtube', 'instagram']
const POST_TARGETS = ['facebook', 'linkedin', 'twitter']
const TARGET_LABEL: Record<string, string> = {
  youtube: 'YouTube',
  instagram: 'Instagram',
  facebook: 'Facebook',
  linkedin: 'LinkedIn',
  twitter: 'Twitter / X',
}

const STATUS_TONE: Record<string, BadgeTone> = {
  awaiting_approval: 'warning',
  published: 'success',
  rejected: 'danger',
}
const STATUS_LABEL: Record<string, string> = {
  awaiting_approval: 'Awaiting approval',
  published: 'Published',
  rejected: 'Rejected',
}

/** One drafted reel/post with its preview + approve/reject (or publish results). */
function DraftCard({
  draft,
  projectId,
  onDecide,
  onRender,
  busy,
  rendering,
}: {
  draft: SocialDraft
  projectId: string
  onDecide: (id: string, action: 'approve' | 'reject') => void
  onRender: (id: string) => void
  busy: boolean
  rendering: boolean
}) {
  const isReel = draft.kind === 'reel'
  const isRendering = rendering || draft.renderStatus === 'rendering'
  // A generated post image to preview inline (stub mode writes a .txt placeholder -> skipped).
  const postImage = !isReel ? draft.artifacts.find((a) => /\.(png|jpe?g|webp|gif)$/i.test(a)) : undefined
  return (
    <GlassCard className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <NeonBadge tone={isReel ? 'violet' : 'cyan'}>
            {isReel ? <Clapperboard className="h-3 w-3" aria-hidden /> : <ImageIcon className="h-3 w-3" aria-hidden />}
            {draft.kind}
          </NeonBadge>
          <NeonBadge tone={STATUS_TONE[draft.status] ?? 'info'} dot>
            {STATUS_LABEL[draft.status] ?? draft.status}
          </NeonBadge>
        </div>
        <div className="flex flex-wrap justify-end gap-1">
          {draft.targets.map((t) => (
            <Chip key={t} label={TARGET_LABEL[t] ?? t} accent="blue" />
          ))}
        </div>
      </div>

      <p className="text-sm font-medium leading-snug text-[#e4e4e7]">{draft.brief}</p>

      {/* Reel preview — storyboard */}
      {isReel && draft.storyboard && (
        <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          <p className="text-xs italic text-[#a1a1aa]">“{draft.storyboard.hook}”</p>
          <div className="mt-2 flex flex-col gap-1.5">
            {draft.storyboard.scenes.map((s, i) => (
              // Content-derived key (scenes are immutable per draft; avoids index-key churn).
              <div key={`${s.onScreenText}|${s.voiceover}|${i}`} className="flex items-baseline gap-2 text-xs">
                <span className="tabular shrink-0 rounded bg-white/[0.06] px-1.5 text-[10px] font-semibold text-omnivra-cyan">
                  {s.durationSec.toFixed(0)}s
                </span>
                <span className="min-w-0 flex-1 text-[#d4d4d8]">
                  <span className="font-medium text-[#e4e4e7]">{s.onScreenText}</span>
                  {s.voiceover ? ` — ${s.voiceover}` : ''}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-[#71717a]">
            <span>~{draft.storyboard.totalDurationSec.toFixed(0)}s</span>
            <span>·</span>
            <span>{draft.storyboard.musicMood}</span>
            <span>·</span>
            <span>{draft.storyboard.callToAction}</span>
          </div>
        </div>
      )}

      {/* Reel render: the .mp4 player once rendered, else a Render button + status */}
      {isReel && (
        <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          {draft.renderStatus === 'rendered' && draft.videoPath ? (
            <video
              controls
              playsInline
              aria-label={`Rendered reel: ${draft.brief}`}
              src={mediaUrl(draft.videoPath, projectId)}
              className="max-h-[26rem] w-full rounded-md bg-black"
            />
          ) : (
            <div className="flex items-center justify-between gap-3">
              <span className="min-w-0 flex-1 truncate text-[11px] text-[#a1a1aa]" aria-live="polite">
                {isRendering
                  ? 'Rendering video…'
                  : draft.renderStatus === 'failed'
                    ? `Render failed: ${draft.renderNote ?? 'unknown error'}`
                    : draft.renderStatus === 'rendered'
                      ? draft.renderNote ?? 'Storyboard ready (install the render engine for video).'
                      : draft.renderStatus === 'none'
                        ? 'Not rendered yet.'
                        : draft.renderNote ?? `Status: ${draft.renderStatus}`}
              </span>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={isRendering}
                onClick={() => onRender(draft.id)}
                className="shrink-0"
              >
                {isRendering ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                ) : (
                  <Film className="h-3.5 w-3.5" aria-hidden />
                )}
                {draft.renderStatus === 'none' ? 'Render video' : 'Re-render'}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Post preview — image + caption + hashtags */}
      {!isReel && (
        <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
          {postImage && (
            <img
              src={mediaUrl(postImage, projectId)}
              alt="Generated post image"
              className="mb-2 w-full rounded-md border border-white/[0.06]"
              loading="lazy"
            />
          )}
          {draft.caption && <p className="whitespace-pre-wrap text-xs text-[#d4d4d8]">{draft.caption}</p>}
          {draft.hashtags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {draft.hashtags.map((h) => (
                <span key={h} className="inline-flex items-center gap-0.5 rounded bg-white/[0.06] px-1.5 py-0.5 text-[11px] text-omnivra-cyan">
                  <Hash className="h-2.5 w-2.5" aria-hidden />
                  {h.replace(/^#/, '')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Artifacts (workspace-relative; preview them in the Workspace view) */}
      {draft.artifacts.length > 0 && (
        <p className="truncate font-mono text-[10px] text-[#52525b]" title={draft.artifacts.join('  •  ')}>
          {draft.artifacts.length} artifact{draft.artifacts.length === 1 ? '' : 's'} · {draft.artifacts[0]}
        </p>
      )}

      {/* Publish results (after approval) */}
      {draft.status === 'published' && draft.publishResults.length > 0 && (
        <div className="flex flex-col gap-1 rounded-lg border border-omnivra-emerald/20 bg-omnivra-emerald/[0.04] p-2.5">
          {draft.publishResults.map((r) => (
            <div key={r.platform} className="flex items-center gap-2 text-[11px]">
              <NeonBadge tone={r.ok ? 'success' : 'danger'}>{TARGET_LABEL[r.platform] ?? r.platform}</NeonBadge>
              <span className="min-w-0 flex-1 truncate text-[#a1a1aa]">{r.note}</span>
              {r.stub && <span className="shrink-0 rounded bg-white/[0.06] px-1.5 text-[10px] text-[#71717a]">stub</span>}
            </div>
          ))}
        </div>
      )}

      {draft.status === 'rejected' && draft.note && (
        <p className="text-[11px] text-omnivra-pink">Rejected: {draft.note}</p>
      )}

      {/* Approve / reject — only while awaiting approval */}
      {draft.status === 'awaiting_approval' && (
        <div className="flex items-center gap-2 pt-0.5">
          <Button
            type="button"
            size="sm"
            disabled={busy}
            onClick={() => onDecide(draft.id, 'approve')}
            className="flex-1"
          >
            {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <Check className="h-3.5 w-3.5" aria-hidden />}
            Approve &amp; publish
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => onDecide(draft.id, 'reject')}
            className="flex-1 hover:text-omnivra-red"
          >
            <X className="h-3.5 w-3.5" aria-hidden />
            Reject
          </Button>
        </div>
      )}
    </GlassCard>
  )
}

/**
 * Social Studio — draft short-form reels and image posts, preview them, and gate
 * each on human approval before it publishes to its target platforms. The composer
 * picks a kind (reel | post) + target platforms; generated drafts list below with a
 * storyboard (reel) or caption+tags (post) preview and Approve/Reject controls.
 * Scoped to the active project; offline (jsdom/tests) the list is empty and the
 * composer still renders. Real video render + uploads land in later phases.
 */
export function Social() {
  const [brief, setBrief] = useState('')
  const [kind, setKind] = useState<SocialKind>('reel')
  const [targets, setTargets] = useState<string[]>([...REEL_TARGETS])

  const { data: drafts } = useSocialDrafts()
  const draftReel = useDraftReel()
  const draftPost = useDraftPost()
  const decide = useDecideDraft()
  const render = useRenderDraft()
  const activeProjectId = useProjectStore((s) => s.activeProjectId)

  const list = drafts ?? []
  const generating = draftReel.isPending || draftPost.isPending
  const platformOptions = kind === 'reel' ? REEL_TARGETS : POST_TARGETS

  const chooseKind = (k: SocialKind) => {
    setKind(k)
    setTargets(k === 'reel' ? [...REEL_TARGETS] : [...POST_TARGETS])
  }

  const toggleTarget = (t: string) =>
    setTargets((cur) => (cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]))

  const generate = (e: FormEvent) => {
    e.preventDefault()
    const b = brief.trim()
    // Guard the contract here too (not just the disabled button): need a brief, at
    // least one target, and no in-flight generation.
    if (!b || targets.length === 0 || generating) return
    const body = { brief: b, targets }
    const onSuccess = () => setBrief('')
    if (kind === 'reel') draftReel.mutate(body, { onSuccess })
    else draftPost.mutate(body, { onSuccess })
  }

  const onDecide = (id: string, action: 'approve' | 'reject') => decide.mutate({ id, decision: { action } })
  const onRender = (id: string) => render.mutate(id)
  const busyId = decide.isPending ? decide.variables?.id : undefined
  const renderingId = render.isPending ? render.variables : undefined
  const failed = draftReel.isError || draftPost.isError

  return (
    <div className="flex flex-col gap-5">
      <GlassCard padding="none" className="overflow-hidden">
        <div className="flex flex-col gap-4 p-5">
          <SectionHeader label="Social Studio" count={list.length} />

          <form onSubmit={generate} className="flex flex-col gap-3">
            <textarea
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              placeholder="What should this content be about? e.g. ‘Launch our AI company OS to founders’"
              aria-label="Content brief"
              rows={2}
              className="focus-ring min-h-[3.5rem] w-full resize-y rounded-md bg-omnivra-surface-2 px-3 py-2 text-sm text-[#e4e4e7] placeholder:text-[#71717a] transition-colors duration-200 ease-out-quint"
            />

            <div className="flex flex-wrap items-center gap-3">
              {/* Kind toggle */}
              <div className="inline-flex rounded-md bg-omnivra-surface-2 p-0.5" role="group" aria-label="Content kind">
                {(['reel', 'post'] as SocialKind[]).map((k) => (
                  <button
                    key={k}
                    type="button"
                    aria-pressed={kind === k}
                    onClick={() => chooseKind(k)}
                    className={cn(
                      'focus-ring inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium capitalize transition-colors duration-200',
                      kind === k ? 'bg-omnivra-surface-3 text-omnivra-cyan' : 'text-[#a1a1aa] hover:text-[#e4e4e7]',
                    )}
                  >
                    {k === 'reel' ? <Clapperboard className="h-3.5 w-3.5" aria-hidden /> : <ImageIcon className="h-3.5 w-3.5" aria-hidden />}
                    {k}
                  </button>
                ))}
              </div>

              {/* Target platforms */}
              <div className="flex flex-wrap items-center gap-1.5">
                {platformOptions.map((t) => {
                  const on = targets.includes(t)
                  return (
                    <button
                      key={t}
                      type="button"
                      aria-pressed={on}
                      onClick={() => toggleTarget(t)}
                      className={cn(
                        'focus-ring rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors duration-200',
                        on
                          ? 'border-omnivra-cyan/40 bg-omnivra-cyan/10 text-omnivra-cyan'
                          : 'border-white/10 text-[#71717a] hover:text-[#a1a1aa]',
                      )}
                    >
                      {TARGET_LABEL[t] ?? t}
                    </button>
                  )
                })}
              </div>

              <Button
                type="submit"
                size="sm"
                disabled={generating || brief.trim().length === 0 || targets.length === 0}
                className="ml-auto"
              >
                {generating ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Wand2 className="h-4 w-4" aria-hidden />}
                {generating ? 'Drafting…' : `Generate ${kind}`}
              </Button>
            </div>

            {failed && (
              <p className="text-xs text-omnivra-pink" role="status" aria-live="polite">
                Could not generate the draft. Is the backend running?
              </p>
            )}
          </form>
        </div>
      </GlassCard>

      {list.length === 0 ? (
        <EmptyState
          icon={Megaphone}
          title="No drafts yet"
          hint="Describe a reel or post above and hit Generate. Drafts wait here for your approval before publishing."
          className="py-16"
        />
      ) : (
        <Stagger className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
          {list.map((draft) => (
            <StaggerItem key={draft.id}>
              <DraftCard
                draft={draft}
                projectId={activeProjectId}
                onDecide={onDecide}
                onRender={onRender}
                busy={busyId === draft.id}
                rendering={renderingId === draft.id}
              />
            </StaggerItem>
          ))}
        </Stagger>
      )}
    </div>
  )
}
