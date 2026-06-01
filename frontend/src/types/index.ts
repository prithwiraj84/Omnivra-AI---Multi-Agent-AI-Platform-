/** Shared domain + UI types for the Omnivra frontend. */
import type { LucideIcon } from 'lucide-react'
import type { Accent } from '@/styles/tokens'

export type { Accent } from '@/styles/tokens'

// --- Agents -----------------------------------------------------------------
export type AgentStatus = 'online' | 'offline' | 'busy' | 'error' | 'idle' | 'working' | 'needs_approval'
export type AgentKind = 'text' | 'media' | 'system'

export type ProviderKey = 'google_ai' | 'openrouter' | 'groq' | 'huggingface'

export interface AgentSummary {
  id: string
  name: string
  department: string
  accent: Accent
  provider: ProviderKey
  providerLabel: string
  /** Full model string sent to the provider. */
  model: string
  /** Short human label shown on the agent card (e.g. "Gemini 2.5 Flash"). */
  modelLabel: string
  kind: AgentKind
  status: AgentStatus
}

// --- Navigation -------------------------------------------------------------
export interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  /** Optional badge count (e.g. pending approvals). */
  badge?: number
  accent?: Accent
}

export interface NavGroup {
  /** Uppercase section label, or null for the top (ungrouped) section. */
  label: string | null
  items: NavItem[]
}

// --- Generic UI value objects (used by primitives + Phase 3 sections) -------
export type Tone = 'success' | 'info' | 'warning' | 'danger' | 'neutral'
export type Priority = 'high' | 'medium' | 'low'

export interface SeriesPoint {
  [key: string]: string | number
}

// --- Dashboard section data shapes (Phase 3, mock-backed) -------------------
export type WorkflowStatus = 'In Progress' | 'Review' | 'Completed' | 'Failed' | 'Queued'

export interface StatCardData {
  label: string
  value: string
  sub?: string
  delta?: string
  deltaTone?: Tone
  icon: LucideIcon
  accent: Accent
}

export interface WorkflowItem {
  id: string
  name: string
  department: string
  status: WorkflowStatus
  progress: number
  accent: Accent
  icon: LucideIcon
}

export interface TaskPoint {
  time: string
  completed: number
  inProgress: number
  failed: number
}

export interface DistributionSlice {
  name: string
  value: number
  color: string
}

export interface ActivityItem {
  id: string
  agent: string
  action: string
  time: string
  accent: Accent
  icon: LucideIcon
}

export interface ApprovalItem {
  id: string
  title: string
  source: string
  priority: Priority
  icon: LucideIcon
  accent: Accent
}

export interface HealthMetric {
  label: string
  /** Percentage 0-100, or null for a non-numeric status (e.g. Network = "Good"). */
  pct: number | null
  display: string
  accent: Accent
}

export interface ProviderUsageItem {
  name: string
  pct: number
  calls: number
  color: string
}

export interface ModelUsageItem {
  id: string
  pct: number
  calls: number
  color: string
}

export interface MediaServiceItem {
  name: string
  provider: string
  calls: number
  delta: string
  accent: Accent
  icon: LucideIcon
}

export interface AchievementItem {
  title: string
  subtitle: string
  icon: LucideIcon
  accent: Accent
}
