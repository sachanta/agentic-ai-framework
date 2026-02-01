import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DatabaseStatus } from './DatabaseStatus';
import { ServiceStatus } from './ServiceStatus';
import { useHealth } from '@/hooks/useHealth';

export function HealthDashboard() {
  const { data: health, isLoading, refetch } = useHealth();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">System Health</h2>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <DatabaseStatus
          name="API Server"
          status={health?.services?.api?.status}
          latency={health?.services?.api?.latency_ms}
          isLoading={isLoading}
        />
        <DatabaseStatus
          name="Weaviate"
          status={health?.services?.weaviate?.status}
          latency={health?.services?.weaviate?.latency_ms}
          isLoading={isLoading}
        />
        <DatabaseStatus
          name="MongoDB"
          status={health?.services?.mongodb?.status}
          latency={health?.services?.mongodb?.latency_ms}
          isLoading={isLoading}
        />
      </div>

      <ServiceStatus
        overallStatus={health?.status}
        healthy={health?.healthy}
        timestamp={health?.timestamp}
        isLoading={isLoading}
      />
    </div>
  );
}
