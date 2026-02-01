import { Activity, Database, Server } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { SystemHealth as SystemHealthType } from '@/types/health';

interface SystemHealthProps {
  health?: SystemHealthType;
  isLoading?: boolean;
}

export function SystemHealth({ health, isLoading }: SystemHealthProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return <Badge variant="success">Connected</Badge>;
      case 'degraded':
        return <Badge variant="warning">Degraded</Badge>;
      case 'unhealthy':
      case 'disconnected':
        return <Badge variant="destructive">Disconnected</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          System Health
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">API Server</span>
          </div>
          {getStatusBadge(health?.services?.api?.status)}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Weaviate</span>
          </div>
          {getStatusBadge(health?.services?.weaviate?.status)}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">MongoDB</span>
          </div>
          {getStatusBadge(health?.services?.mongodb?.status)}
        </div>

        <div className="flex items-center justify-between pt-2">
          <span className="text-sm text-muted-foreground">Overall Status</span>
          {getStatusBadge(health?.status)}
        </div>
      </CardContent>
    </Card>
  );
}
