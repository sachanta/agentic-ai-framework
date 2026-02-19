import { Skeleton } from '@/components/ui/skeleton';
import { AgentStudioCard } from './AgentStudioCard';
import type { StudioAgentSummary } from '@/types/studio';

interface AgentCatalogGridProps {
  agents: StudioAgentSummary[];
  isLoading: boolean;
  onSelectAgent: (agent: StudioAgentSummary) => void;
}

export function AgentCatalogGrid({
  agents,
  isLoading,
  onSelectAgent,
}: AgentCatalogGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-[200px] rounded-lg" />
        ))}
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No agents discovered.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {agents.map((agent) => (
        <AgentStudioCard
          key={agent.agent_id}
          agent={agent}
          onSelect={onSelectAgent}
        />
      ))}
    </div>
  );
}
