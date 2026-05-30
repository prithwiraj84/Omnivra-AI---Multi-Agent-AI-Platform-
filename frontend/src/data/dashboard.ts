/**
 * Mock data for the Phase-3 dashboard sections — values mirror the reference dashboard.
 * Replaced by live API/WebSocket data in Phase 4+. Shapes are defined in '@/types'.
 */
import {
  Activity,
  Bot,
  CheckCircle2,
  Code2,
  Coins,
  Database,
  DollarSign,
  FileText,
  Image,
  Instagram,
  LayoutDashboard,
  LayoutGrid,
  Mic,
  PartyPopper,
  Presentation,
  ServerCog,
  ShieldCheck,
  TrendingUp,
  Volume2,
  Webhook,
  Zap,
} from 'lucide-react'
import { accentHex, categorical } from '@/styles/tokens'
import type {
  AchievementItem,
  ActivityItem,
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
import { PRIMARY_AGENTS, SYSTEM_OPS_AGENTS } from '@/config/agents'
import type { DashboardData } from '@/lib/api/types'

export const executiveStats: StatCardData[] = [
  { label: 'Total Agents', value: '18', sub: 'Online', icon: Bot, accent: 'cyan' },
  { label: 'Active Tasks', value: '7', sub: 'Running', icon: Activity, accent: 'blue' },
  { label: 'Completed Today', value: '24', delta: '+142%', deltaTone: 'success', icon: CheckCircle2, accent: 'emerald' },
  { label: 'Success Rate', value: '98.6%', sub: 'Excellent', icon: TrendingUp, accent: 'emerald' },
  { label: 'Total Cost (Est.)', value: '$0.18', sub: 'Today', icon: DollarSign, accent: 'violet' },
]

export const workflows: WorkflowItem[] = [
  { id: 'wf-1', name: 'AI Company OS Dashboard', department: 'Development', status: 'In Progress', progress: 78, accent: 'cyan', icon: LayoutDashboard },
  { id: 'wf-2', name: 'Instagram Campaign', department: 'Marketing', status: 'In Progress', progress: 30, accent: 'amber', icon: Instagram },
  { id: 'wf-3', name: 'API Documentation', department: 'Documentation', status: 'Review', progress: 90, accent: 'violet', icon: FileText },
  { id: 'wf-4', name: 'Investor Pitch Deck', department: 'Documentation', status: 'In Progress', progress: 40, accent: 'violet', icon: Presentation },
  { id: 'wf-5', name: 'Security Audit', department: 'Quality & Security', status: 'Completed', progress: 100, accent: 'emerald', icon: ShieldCheck },
]

export const taskExecution: TaskPoint[] = [
  { time: '12 AM', completed: 12, inProgress: 8, failed: 2 },
  { time: '03 AM', completed: 18, inProgress: 11, failed: 1 },
  { time: '06 AM', completed: 30, inProgress: 16, failed: 3 },
  { time: '09 AM', completed: 27, inProgress: 14, failed: 2 },
  { time: '12 PM', completed: 41, inProgress: 22, failed: 4 },
  { time: '03 PM', completed: 38, inProgress: 19, failed: 3 },
  { time: '06 PM', completed: 47, inProgress: 24, failed: 5 },
  { time: '09 PM', completed: 44, inProgress: 17, failed: 2 },
]

export const taskExecutionSeries = [
  { key: 'completed', label: 'Completed', color: '#10b981' },
  { key: 'inProgress', label: 'In Progress', color: '#3b82f6' },
  { key: 'failed', label: 'Failed', color: '#ef4444' },
]

export const taskDistribution: DistributionSlice[] = [
  { name: 'Development', value: 45, color: categorical[0] },
  { name: 'Marketing', value: 20, color: categorical[1] },
  { name: 'Documentation', value: 15, color: categorical[2] },
  { name: 'Quality & Security', value: 10, color: categorical[3] },
  { name: 'System Ops', value: 10, color: categorical[4] },
]
export const totalTasks = 124

export const activity: ActivityItem[] = [
  { id: 'a1', agent: 'Backend Engineer', action: 'Created 12 files', time: '2m ago', accent: 'blue', icon: Code2 },
  { id: 'a2', agent: 'Frontend Engineer', action: 'Updated Dashboard.tsx', time: '3m ago', accent: 'blue', icon: LayoutGrid },
  { id: 'a3', agent: 'Database Engineer', action: 'Created 8 tables', time: '5m ago', accent: 'blue', icon: Database },
  { id: 'a4', agent: 'QA Engineer', action: 'Completed test suite', time: '8m ago', accent: 'emerald', icon: CheckCircle2 },
  { id: 'a5', agent: 'SecOps Engineer', action: 'Security scan passed', time: '10m ago', accent: 'emerald', icon: ShieldCheck },
  { id: 'a6', agent: 'Documentation Agent', action: 'Updated README.md', time: '12m ago', accent: 'violet', icon: FileText },
]

export const approvals: ApprovalItem[] = [
  { id: 'ap1', title: 'API Endpoints', source: 'by API Engineer', priority: 'high', icon: Webhook, accent: 'blue' },
  { id: 'ap2', title: 'Database Schema', source: 'by Database Engineer', priority: 'high', icon: Database, accent: 'blue' },
  { id: 'ap3', title: 'UI Components', source: 'by Frontend Engineer', priority: 'medium', icon: LayoutGrid, accent: 'amber' },
  { id: 'ap4', title: 'Security Report', source: 'by SecOps Engineer', priority: 'high', icon: ShieldCheck, accent: 'emerald' },
]
export const totalPendingApprovals = 7

export const systemHealth: HealthMetric[] = [
  { label: 'CPU Usage', pct: 32, display: '32%', accent: 'cyan' },
  { label: 'Memory Usage', pct: 58, display: '58%', accent: 'blue' },
  { label: 'Storage Usage', pct: 68, display: '68%', accent: 'emerald' },
  { label: 'Network', pct: null, display: 'Good', accent: 'emerald' },
  { label: 'API Quota (OpenRouter)', pct: 89, display: '89%', accent: 'amber' },
  { label: 'API Quota (Groq)', pct: 76, display: '76%', accent: 'emerald' },
]

export const providerUsage: ProviderUsageItem[] = [
  { name: 'Google AI Studio', pct: 28, calls: 892, color: accentHex.cyan },
  { name: 'OpenRouter', pct: 42, calls: 1228, color: accentHex.pink },
  { name: 'Groq', pct: 18, calls: 561, color: accentHex.amber },
  { name: 'Hugging Face', pct: 12, calls: 384, color: accentHex.violet },
]

export const modelUsage: ModelUsageItem[] = [
  { id: 'openai/gpt-oss-120b:free', pct: 32, calls: 512, color: categorical[0] },
  { id: 'z-ai/glm-4.5-air:free', pct: 24, calls: 1384, color: categorical[1] },
  { id: 'nvidia/nemotron-3-super-120b', pct: 18, calls: 288, color: categorical[2] },
  { id: 'poolside/laguna-m.1:free', pct: 12, calls: 192, color: categorical[3] },
  { id: 'google/gemma-4-31b-it:free', pct: 8, calls: 128, color: categorical[4] },
  { id: 'liquid/lfm-2.5-1.2b-thinking:free', pct: 6, calls: 96, color: categorical[5] },
]

export const mediaServices: MediaServiceItem[] = [
  { name: 'Speech-to-Text', provider: 'Whisper', calls: 128, delta: '+15%', accent: 'cyan', icon: Mic },
  { name: 'Text-to-Speech', provider: 'Orpheus', calls: 95, delta: '+35%', accent: 'violet', icon: Volume2 },
  { name: 'Image Generation', provider: 'FLUX.1-dev', calls: 342, delta: '+25%', accent: 'emerald', icon: Image },
]

export const achievements: AchievementItem[] = [
  { title: '100+ Tasks Completed', subtitle: 'Today', icon: PartyPopper, accent: 'cyan' },
  { title: '98.6% Success Rate', subtitle: 'Excellent Performance', icon: ShieldCheck, accent: 'emerald' },
  { title: '18 Agents Online', subtitle: 'All Systems Go', icon: Zap, accent: 'blue' },
  { title: 'Zero Critical Errors', subtitle: 'Last 24 Hours', icon: ServerCog, accent: 'violet' },
  { title: 'Cost Optimized', subtitle: '90% Below Industry Avg', icon: Coins, accent: 'amber' },
]

/**
 * Offline fallback / React Query initialData — the full dashboard assembled from the
 * mock slices above plus the agent roster. useDashboard() renders this instantly, then
 * replaces it with live GET /api/dashboard data when the backend responds.
 */
export const fallbackDashboard: DashboardData = {
  stats: executiveStats,
  agents: PRIMARY_AGENTS,
  systemOps: SYSTEM_OPS_AGENTS,
  workflows,
  taskExecution,
  taskExecutionSeries,
  taskDistribution,
  totalTasks,
  activity,
  approvals,
  totalPendingApprovals,
  systemHealth,
  providerUsage,
  modelUsage,
  mediaServices,
  achievements,
}
