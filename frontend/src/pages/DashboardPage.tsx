import { Bot, Wrench, GitBranch, Play } from 'lucide-react';
import { StatusCard } from '@/components/dashboard/StatusCard';
import { ExecutionTimeline } from '@/components/dashboard/ExecutionTimeline';
import { SystemHealth } from '@/components/dashboard/SystemHealth';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { useAgents } from '@/hooks/useAgents';
import { useTools } from '@/hooks/useTools';
import { useWorkflows } from '@/hooks/useWorkflows';
import { useExecutions, useExecutionStats } from '@/hooks/useExecutions';
import { useHealth } from '@/hooks/useHealth';

export function DashboardPage() {
  const { data: agentsData } = useAgents({ pageSize: 1 });
  const { data: toolsData } = useTools({ pageSize: 1 });
  const { data: workflowsData } = useWorkflows({ pageSize: 1 });
  const { data: executionsData } = useExecutions({ pageSize: 10 });
  const { data: stats } = useExecutionStats();
  const { data: health, isLoading: healthLoading } = useHealth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your AI framework</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="Total Agents"
          value={agentsData?.total ?? 0}
          icon={Bot}
        />
        <StatusCard
          title="Total Tools"
          value={toolsData?.total ?? 0}
          icon={Wrench}
        />
        <StatusCard
          title="Total Workflows"
          value={workflowsData?.total ?? 0}
          icon={GitBranch}
        />
        <StatusCard
          title="Executions Today"
          value={stats?.total ?? 0}
          description={`${stats?.successRate?.toFixed(1) ?? 0}% success rate`}
          icon={Play}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ExecutionTimeline executions={executionsData?.items ?? []} />
        </div>
        <div className="space-y-6">
          <SystemHealth health={health} isLoading={healthLoading} />
          <QuickActions />
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
