/** Fetch + adapt the dashboard payload: resolve string icon keys to Lucide components. */
import type { LucideIcon } from 'lucide-react'
import { api } from '@/lib/api/client'
import { resolveIcon } from '@/lib/api/icons'
import type { DashboardDTO, DashboardData } from '@/lib/api/types'

function withIcon<T extends { icon: string }>(d: T): Omit<T, 'icon'> & { icon: LucideIcon } {
  return { ...d, icon: resolveIcon(d.icon) }
}

/** Convert the wire DTO (string icons) into the icon-resolved shape the UI consumes. */
export function adaptDashboard(dto: DashboardDTO): DashboardData {
  return {
    stats: dto.stats.map(withIcon),
    agents: dto.agents,
    systemOps: dto.systemOps,
    workflows: dto.workflows.map(withIcon),
    taskExecution: dto.taskExecution,
    taskExecutionSeries: dto.taskExecutionSeries,
    taskDistribution: dto.taskDistribution,
    totalTasks: dto.totalTasks,
    activity: dto.activity.map(withIcon),
    approvals: dto.approvals.map(withIcon),
    totalPendingApprovals: dto.totalPendingApprovals,
    systemHealth: dto.systemHealth,
    providerUsage: dto.providerUsage,
    modelUsage: dto.modelUsage,
    mediaServices: dto.mediaServices.map(withIcon),
    achievements: dto.achievements.map(withIcon),
  }
}

/** GET /api/dashboard, adapted for the UI. */
export async function getDashboard(): Promise<DashboardData> {
  const { data } = await api.get<DashboardDTO>('/dashboard')
  return adaptDashboard(data)
}
