import { useState } from 'react';
import { FlaskConical } from 'lucide-react';
import { useStudioAgents } from '@/hooks/useStudio';
import { PlatformFilter } from '@/components/studio/PlatformFilter';
import { AgentCatalogGrid } from '@/components/studio/AgentCatalogGrid';
import { AgentDetailDrawer } from '@/components/studio/AgentDetailDrawer';
import type { StudioAgentSummary } from '@/types/studio';

export function StudioPage() {
  const [selectedPlatform, setSelectedPlatform] = useState<
    string | undefined
  >(undefined);
  const [selectedAgent, setSelectedAgent] =
    useState<StudioAgentSummary | null>(null);

  const { data, isLoading } = useStudioAgents(selectedPlatform);

  const agents = data?.agents ?? [];
  const platforms = data?.platforms ?? [];

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
        onSelectAgent={setSelectedAgent}
      />

      <AgentDetailDrawer
        agent={selectedAgent}
        open={selectedAgent !== null}
        onClose={() => setSelectedAgent(null)}
      />
    </div>
  );
}

export default StudioPage;
