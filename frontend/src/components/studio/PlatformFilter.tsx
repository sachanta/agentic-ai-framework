import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import type { StudioPlatformSummary } from '@/types/studio';

interface PlatformFilterProps {
  platforms: StudioPlatformSummary[];
  selected: string | undefined;
  onSelect: (platformId: string | undefined) => void;
  totalAgentCount: number;
}

export function PlatformFilter({
  platforms,
  selected,
  onSelect,
  totalAgentCount,
}: PlatformFilterProps) {
  return (
    <Tabs
      value={selected ?? 'all'}
      onValueChange={(v) => onSelect(v === 'all' ? undefined : v)}
    >
      <TabsList>
        <TabsTrigger value="all">
          All
          <Badge variant="secondary" className="ml-2">
            {totalAgentCount}
          </Badge>
        </TabsTrigger>
        {platforms.map((p) => (
          <TabsTrigger key={p.id} value={p.id}>
            {p.name}
            <Badge variant="secondary" className="ml-2">
              {p.agent_count}
            </Badge>
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
