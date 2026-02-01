import { useParams, Navigate } from 'react-router-dom';
import { AgentDetail } from '@/components/agents/AgentDetail';
import { useAgent } from '@/hooks/useAgents';
import { ROUTES } from '@/utils/constants';
import { Skeleton } from '@/components/ui/skeleton';

export function AgentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: agent, isLoading, error } = useAgent(id!);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (error || !agent) {
    return <Navigate to={ROUTES.AGENTS} replace />;
  }

  return <AgentDetail agent={agent} />;
}

export default AgentDetailPage;
