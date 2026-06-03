/**
 * API DTO types — the wire shape of GET /api/dashboard. camelCase, mirroring the
 * backend Pydantic schemas (backend/app/schemas/dashboard.py). `icon` fields are
 * string keys resolved to Lucide components by `resolveIcon` (./icons). The adapter
 * (./dashboard) converts a DashboardDTO into the icon-resolved `DashboardData` that
 * the section components consume.
 */
import type {
  AchievementItem,
  ActivityItem,
  AgentSummary,
  ApprovalItem,
  DistributionSlice,
  HealthMetric,
  MediaServiceItem,
  ModelUsageItem,
  ProviderUsageItem,
  StatCardData,
  TaskPoint,
  WorkflowItem,
} from '@/types'

/** A type whose `icon` is a string key (wire form) instead of a LucideIcon. */
type WithIconKey<T extends { icon: unknown }> = Omit<T, 'icon'> & { icon: string }

export interface SeriesDef {
  key: string
  label: string
  color: string
}

export type StatCardDTO = WithIconKey<StatCardData>
export type WorkflowDTO = WithIconKey<WorkflowItem>
export type ActivityDTO = WithIconKey<ActivityItem>
export type ApprovalDTO = WithIconKey<ApprovalItem>
export type MediaServiceDTO = WithIconKey<MediaServiceItem>
export type AchievementDTO = WithIconKey<AchievementItem>

/** Wire shape returned by GET /api/dashboard. */
export interface DashboardDTO {
  stats: StatCardDTO[]
  agents: AgentSummary[]
  systemOps: AgentSummary[]
  workflows: WorkflowDTO[]
  taskExecution: TaskPoint[]
  taskExecutionSeries: SeriesDef[]
  taskDistribution: DistributionSlice[]
  totalTasks: number
  activity: ActivityDTO[]
  approvals: ApprovalDTO[]
  totalPendingApprovals: number
  systemHealth: HealthMetric[]
  providerUsage: ProviderUsageItem[]
  modelUsage: ModelUsageItem[]
  mediaServices: MediaServiceDTO[]
  achievements: AchievementDTO[]
}

// --- Workflow run / approval gate (Phase 7) ---------------------------------

/** One agent's contribution to a workflow run. */
export interface AgentRunOutput {
  agentId: string
  content: string
  ok: boolean
  tokens: number
}

/** A gated run's pending-approval handle (camelCase wire shape). */
export interface PendingApproval {
  approvalId: string
  kind: string
  summary: string
  requestedBy: string
}

/** Lifecycle status of a workflow run. */
export type RunStatus =
  | 'running' // fire-and-poll: in-flight until the background orchestration reaches a terminal state
  | 'completed'
  | 'failed'
  | 'stopped' // kill switch / guard halted the run (WorkflowStatus.STOPPED)
  | 'awaiting_approval'
  | 'rolled_back'

/**
 * RunResult — the wire shape returned by POST /workflows/run,
 * POST /approvals/{id}/decision and GET /workflows/runs[/{id}]. camelCase,
 * mirroring the backend. `pendingApproval` is non-null only while a gated run
 * is paused (status === 'awaiting_approval').
 */
export interface RunResult {
  workflowId: string
  projectId?: string | null
  status: RunStatus
  task: string
  plan: string[]
  delegations: string[]
  agentOutputs: AgentRunOutput[]
  recursionCount: number
  result: Record<string, unknown>
  errors: string[]
  pendingApproval: PendingApproval | null
}

// --- Workspace artifacts (Phase 8) ------------------------------------------

/**
 * Artifact — one file an agent wrote under the workspace sandbox. camelCase wire
 * shape of GET /api/workspace/artifacts. `category` is the workspace subdir
 * (frontend/backend/docs/presentations/reports); `agentId` is null when unknown.
 */
export interface Artifact {
  path: string
  category: string
  sizeBytes: number
  modified: string
  agentId: string | null
}

/** ArtifactContent — the text body of one artifact (GET /workspace/artifacts/{path}). */
export interface ArtifactContent {
  path: string
  content: string
}

/**
 * RunProgramResult — outcome of POST /workspace/run (the guarded in-workspace runner).
 * `ok` is true only on a clean exit (code 0, not timed out). camelCase wire shape.
 */
export interface RunProgramResult {
  path: string
  command: string
  ok: boolean
  exitCode: number | null
  timedOut: boolean
  durationMs: number
  stdout: string
  stderr: string
  note: string
}

// --- Knowledge base + Memory + RAG (Phase 9) --------------------------------

/**
 * SearchHit — one vector-store search result (camelCase wire shape of
 * GET /knowledge/search and GET /memory/search). `score` is the cosine
 * similarity; `metadata` carries provenance (e.g. source, agentId).
 */
export interface SearchHit {
  id: string
  text: string
  score: number
  metadata: Record<string, unknown>
}

/** MemoryEntry — one stored memory item (GET /memory/recent). */
export interface MemoryEntry {
  id: string
  text: string
  metadata: Record<string, unknown>
}

/** StoreStats — the document count of a vector store (GET /{knowledge,memory}/stats). */
export interface StoreStats {
  count: number
}

/** IngestResult — outcome of POST /knowledge/ingest-workspace. */
export interface IngestResult {
  ingested: number
  total: number
}

// --- Projects + Tasks (Phase 10) --------------------------------------------

/**
 * Project — one workstream the company tracks. camelCase wire shape of
 * GET /api/projects. `taskCount` is the number of tasks attached to the project
 * (derived server-side); `status` is a free-form lifecycle string (e.g. "active").
 */
export interface Project {
  id: string
  name: string
  description: string
  status: string
  createdAt: string
  taskCount: number
}

/**
 * Task — one unit of work, optionally attached to a project and/or an agent.
 * camelCase wire shape of GET /api/tasks. `status` is one of
 * todo | in_progress | review | done; `priority` is one of high | medium | low.
 * `projectId`/`agentId` are null when unassigned.
 */
export interface Task {
  id: string
  title: string
  projectId: string | null
  status: string
  priority: string
  agentId: string | null
  createdAt: string
}

/** Request body for POST /api/projects. */
export interface ProjectCreate {
  name: string
  description?: string
}

/** Request body for POST /api/tasks. New tasks are created with status "todo". */
export interface TaskCreate {
  title: string
  projectId?: string
  priority?: string
  agentId?: string
}

// --- Social content pipeline (cp-0016) --------------------------------------

export type SocialKind = 'reel' | 'post'
export type SocialStatus = 'awaiting_approval' | 'published' | 'rejected'

/** One shot in a vertical short-form reel (camelCase wire shape). */
export interface ReelScene {
  durationSec: number
  voiceover: string
  brollQuery: string
  onScreenText: string
}

/** The machine-readable plan the video engine renders from. */
export interface ReelStoryboard {
  title: string
  hook: string
  scenes: ReelScene[]
  musicMood: string
  callToAction: string
  totalDurationSec: number
}

/** The outcome of (attempting to) publish a draft to one platform. */
export interface PublishResult {
  platform: string
  ok: boolean
  url: string | null
  stub: boolean
  note: string
}

/**
 * SocialDraft — a drafted reel/post awaiting approval, then published. camelCase
 * wire shape of the /api/social endpoints. `storyboard` is set for reels; `caption`
 * + `hashtags` for posts. `publishResults` is filled once approved.
 */
export interface SocialDraft {
  id: string
  projectId: string
  kind: SocialKind
  brief: string
  status: SocialStatus
  targets: string[]
  storyboard: ReelStoryboard | null
  renderStatus: string // none | rendering | rendered | failed (reels)
  videoPath: string | null // workspace-relative .mp4 once rendered
  renderNote: string | null
  caption: string | null
  hashtags: string[]
  artifacts: string[]
  publishResults: PublishResult[]
  createdAt: string
  note: string | null
}

/** Request body for POST /api/social/reel. */
export interface ReelRequest {
  brief: string
  targets?: string[]
}

/** Request body for POST /api/social/post. */
export interface PostRequest {
  brief: string
  targets?: string[]
}

/** Request body for POST /api/social/drafts/{id}/decision. */
export interface SocialDecision {
  action: 'approve' | 'reject'
  note?: string
}

export type SocialProgressStatus = 'running' | 'done' | 'error'
export type SocialPhase = 'draft' | 'render'

/**
 * One 'social_progress' frame pushed over /ws while a reel/post is generating or
 * rendering — drives the live per-step progress in Social Studio (before approval).
 * `jobId` is the draft id; `step` is a stable key, deduped across its running -> done frames.
 */
export interface SocialProgressEvent {
  jobId: string
  projectId: string
  kind: SocialKind
  phase: SocialPhase
  step: string
  label: string
  status: SocialProgressStatus
  index: number
  total: number
  detail?: string | null
}

// --- Document Studio (cp-0025) ----------------------------------------------

export type DocFormat = 'pptx' | 'docx' | 'pdf'
export type DocStatus = 'generating' | 'awaiting_approval' | 'approved' | 'rejected'
/** Visual theme. 'auto' lets the documentation agent pick; the rest force a palette. */
export type DocTheme = 'auto' | 'indigo' | 'emerald' | 'amber' | 'violet' | 'slate'

/** A simple tabular block: a header row + data rows (rendered as a styled table). */
export interface DocTable {
  headers: string[]
  rows: string[][]
}

/** One section of a generated document: prose + optional bullet list + optional table. */
export interface DocSection {
  heading: string
  body: string
  bullets?: string[]
  table?: DocTable | null
}

/**
 * DocumentDraft — a document drafted from a prompt (Gemma writes the content),
 * rendered to a chosen format and gated on approval. `filePath` is the rendered
 * .pptx/.docx/.pdf (or a markdown deliverable when `stub` is true — the optional
 * render engine isn't installed). camelCase wire shape of the /api/documents routes.
 */
export interface DocumentDraft {
  id: string
  projectId: string
  prompt: string
  format: DocFormat
  title: string
  subtitle?: string
  theme?: string // resolved palette name (indigo | emerald | amber | violet | slate)
  status: DocStatus
  sections: DocSection[]
  artifacts: string[]
  filePath: string | null
  stub: boolean
  renderNote: string | null // render-engine / stub explanation (survives a decision)
  note: string | null // human decision reason (set on reject)
  createdAt: string
}

/** Request body for POST /api/documents/generate. */
export interface DocumentRequest {
  prompt: string
  format: DocFormat
  theme?: DocTheme
}

/** Request body for POST /api/documents/{id}/decision. */
export interface DocumentDecision {
  action: 'approve' | 'reject'
  note?: string
}

/** Icon-resolved shape consumed by the dashboard section components. */
export interface DashboardData {
  stats: StatCardData[]
  agents: AgentSummary[]
  systemOps: AgentSummary[]
  workflows: WorkflowItem[]
  taskExecution: TaskPoint[]
  taskExecutionSeries: SeriesDef[]
  taskDistribution: DistributionSlice[]
  totalTasks: number
  activity: ActivityItem[]
  approvals: ApprovalItem[]
  totalPendingApprovals: number
  systemHealth: HealthMetric[]
  providerUsage: ProviderUsageItem[]
  modelUsage: ModelUsageItem[]
  mediaServices: MediaServiceItem[]
  achievements: AchievementItem[]
}
