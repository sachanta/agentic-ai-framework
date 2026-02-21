import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FlaskConical } from 'lucide-react';
import { useStudioAgents } from '@/hooks/useStudio';
import { PlatformFilter } from '@/components/studio/PlatformFilter';
import { AgentCatalogGrid } from '@/components/studio/AgentCatalogGrid';
import type { StudioAgentSummary } from '@/types/studio';

export function StudioPage() {
  const navigate = useNavigate();
  const [selectedPlatform, setSelectedPlatform] = useState<
    string | undefined
  >(undefined);

  const { data, isLoading } = useStudioAgents(selectedPlatform);

  const agents = data?.agents ?? [];
  const platforms = data?.platforms ?? [];

  const handleSelectAgent = (agent: StudioAgentSummary) => {
    navigate(`/studio/${agent.platform_id}/${agent.name}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <FlaskConical className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Agent Studio</h1>
          <p className="text-muted-foreground">
            Discover and inspect all agents across every platform
          </p>
        </div>
      </div>

      <PlatformFilter
        platforms={platforms}
        selected={selectedPlatform}
        onSelect={setSelectedPlatform}
        totalAgentCount={data?.total ?? 0}
      />

      <AgentCatalogGrid
        agents={agents}
        isLoading={isLoading}
        onSelectAgent={handleSelectAgent}
      />
    </div>
  );
}

export default StudioPage;
