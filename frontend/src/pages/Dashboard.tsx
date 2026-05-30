import { GreetingHero } from '@/components/dashboard/greeting-hero'
import { ExecutiveOverview } from '@/components/dashboard/executive-overview'
import { AgentStatusGrid } from '@/components/dashboard/agent-status-grid'
import { WorkflowList } from '@/components/dashboard/workflow-list'
import { TaskExecutionChart } from '@/components/dashboard/task-execution-chart'
import { TaskDistribution } from '@/components/dashboard/task-distribution'
import { ProviderUsage } from '@/components/dashboard/provider-usage'
import { ModelUsage } from '@/components/dashboard/model-usage'
import { MediaServices } from '@/components/dashboard/media-services'
import { Achievements } from '@/components/dashboard/achievements'
import { Stagger, StaggerItem } from '@/components/common/reveal'
import { useDashboard } from '@/hooks/useDashboard'

/**
 * Dashboard — the command-center home. Reads all data from useDashboard(), which serves
 * the bundled fallback instantly and upgrades to live GET /api/dashboard data when the
 * backend responds. Sections stay presentational; this is the single data seam.
 *
 * Layout (vertical stack, gap-6): GreetingHero · ExecutiveOverview · AgentStatusGrid ·
 * [WorkflowList | TaskExecutionChart | TaskDistribution] · [ProviderUsage | ModelUsage |
 * MediaServices] · Achievements.
 */
export function Dashboard() {
  const { data } = useDashboard()

  return (
    <Stagger className="flex flex-col gap-6">
      <StaggerItem>
        <GreetingHero />
      </StaggerItem>

      <StaggerItem>
        <ExecutiveOverview stats={data.stats} />
      </StaggerItem>

      <StaggerItem>
        <AgentStatusGrid agents={data.agents} systemOps={data.systemOps} />
      </StaggerItem>

      {/* Workflows · Task Execution · Task Distribution */}
      <StaggerItem className="grid gap-5 lg:grid-cols-12">
        <div className="lg:col-span-4">
          <WorkflowList workflows={data.workflows} />
        </div>
        <div className="lg:col-span-5">
          <TaskExecutionChart data={data.taskExecution} series={data.taskExecutionSeries} />
        </div>
        <div className="lg:col-span-3">
          <TaskDistribution data={data.taskDistribution} total={data.totalTasks} />
        </div>
      </StaggerItem>

      {/* Provider usage · Model usage · Media services */}
      <StaggerItem className="grid gap-5 md:grid-cols-3">
        <ProviderUsage providers={data.providerUsage} />
        <ModelUsage models={data.modelUsage} />
        <MediaServices services={data.mediaServices} />
      </StaggerItem>

      <StaggerItem>
        <Achievements items={data.achievements} />
      </StaggerItem>
    </Stagger>
  )
}
