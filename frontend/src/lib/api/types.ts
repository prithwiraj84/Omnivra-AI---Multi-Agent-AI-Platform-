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
  | 'completed'
  | 'failed'
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
