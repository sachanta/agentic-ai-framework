import { Database } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

interface DatabaseStatusProps {
  name: string;
  status?: string;
  latency?: number | null;
  isLoading?: boolean;
}

export function DatabaseStatus({ name, status, latency, isLoading }: DatabaseStatusProps) {
  const getStatusVariant = (status?: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
      case 'disconnected':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
      case 'degraded':
      case 'unhealthy':
      case 'disconnected':
        return '●';
      default:
        return '○';
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return 'text-green-500';
      case 'degraded':
        return 'text-yellow-500';
      case 'unhealthy':
      case 'disconnected':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Database className="h-4 w-4" />
            {name}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-24" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Database className="h-4 w-4" />
          {name}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`text-xl ${getStatusColor(status)}`}>
              {getStatusIcon(status)}
            </span>
            <Badge variant={getStatusVariant(status)}>
              {status || 'Unknown'}
            </Badge>
          </div>
          {latency != null && (
            <span className="text-sm text-muted-foreground">{latency}ms</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
