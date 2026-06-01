/**
 * Neutral dashboard fallback / React Query initialData.
 *
 * This is NOT demo data — it's a loading skeleton with the SAME labels the live
 * backend (GET /api/dashboard) returns, but empty/placeholder values ("—", [], 0).
 * useDashboard() renders this instantly so the layout never blanks, then replaces it
 * with live data on mount. Because no fake numbers are ever shown, values settle in
 * smoothly (—  -> real) with no flicker.
 */
import { Activity, Bot, CheckCircle2, TrendingUp, Zap } from 'lucide-react'
import type { HealthMetric, StatCardData, TaskPoint } from '@/types'
import type { DashboardData } from '@/lib/api/types'

// Same labels + icons as the live stat cards (dashboard_live.py), values pending.
const loadingStats: StatCardData[] = [
  { label: 'Agents', value: '—', sub: 'Loading', icon: Bot, accent: 'cyan' },
  { label: 'Active Tasks', value: '—', sub: 'Loading', icon: Activity, accent: 'blue' },
  { label: 'Workflow Runs', value: '—', sub: 'Loading', icon: CheckCircle2, accent: 'emerald' },
  { label: 'Success Rate', value: '—', sub: 'Loading', icon: TrendingUp, accent: 'emerald' },
  { label: 'LLM Calls', value: '—', sub: 'Loading', icon: Zap, accent: 'violet' },
]

// Same labels as the live system-health metrics, values pending.
const loadingHealth: HealthMetric[] = [
  { label: 'Agents Registered', pct: null, display: '—', accent: 'cyan' },
  { label: 'Providers Online', pct: null, display: '—', accent: 'emerald' },
  { label: 'Workflow Runs', pct: null, display: '—', accent: 'blue' },
  { label: 'Memory Items', pct: null, display: '—', accent: 'violet' },
  { label: 'Knowledge Docs', pct: null, display: '—', accent: 'emerald' },
  { label: 'Realtime Clients', pct: null, display: '—', accent: 'cyan' },
]

const zeroExecution: TaskPoint[] = ['12 AM', '03 AM', '06 AM', '09 AM', '12 PM', '03 PM', '06 PM', '09 PM'].map(
  (time) => ({ time, completed: 0, inProgress: 0, failed: 0 }),
)

const taskExecutionSeries = [
  { key: 'completed', label: 'Completed', color: '#10b981' },
  { key: 'inProgress', label: 'In Progress', color: '#3b82f6' },
  { key: 'failed', label: 'Failed', color: '#ef4444' },
]

export const fallbackDashboard: DashboardData = {
  stats: loadingStats,
  agents: [],
  systemOps: [],
  workflows: [],
  taskExecution: zeroExecution,
  taskExecutionSeries,
  taskDistribution: [],
  totalTasks: 0,
  activity: [],
  approvals: [],
  totalPendingApprovals: 0,
  systemHealth: loadingHealth,
  providerUsage: [],
  modelUsage: [],
  mediaServices: [],
  achievements: [],
}
