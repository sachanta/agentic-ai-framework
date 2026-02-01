import { Activity, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

interface ServiceStatusProps {
  overallStatus?: string;
  healthy?: boolean;
  timestamp?: number;
  isLoading?: boolean;
}

export function ServiceStatus({
  overallStatus,
  healthy,
  timestamp,
  isLoading,
}: ServiceStatusProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Overall Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="success">Healthy</Badge>;
      case 'degraded':
        return <Badge variant="warning">Degraded</Badge>;
      case 'unhealthy':
        return <Badge variant="destructive">Unhealthy</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const formatTimestamp = (ts?: number) => {
    if (!ts) return '-';
    return new Date(ts * 1000).toLocaleString();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Overall Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-3 p-3 border rounded-lg">
            {healthy ? (
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            ) : (
              <XCircle className="h-8 w-8 text-red-500" />
            )}
            <div>
              <div className="mb-1">{getStatusBadge(overallStatus)}</div>
              <p className="text-sm text-muted-foreground">System Status</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 border rounded-lg">
            <Activity className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-lg font-bold">{healthy ? 'Operational' : 'Issues Detected'}</p>
              <p className="text-sm text-muted-foreground">Health Check</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 border rounded-lg">
            <Clock className="h-8 w-8 text-purple-500" />
            <div>
              <p className="text-sm font-medium">{formatTimestamp(timestamp)}</p>
              <p className="text-sm text-muted-foreground">Last Updated</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
