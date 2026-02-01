import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatTimeAgo, formatDuration } from '@/utils/format';
import type { Execution } from '@/types/execution';

interface ExecutionTimelineProps {
  executions: Execution[];
}

export function ExecutionTimeline({ executions }: ExecutionTimelineProps) {
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'default';
      case 'failed':
        return 'destructive';
      case 'cancelled':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Executions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {executions.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No recent executions
            </p>
          ) : (
            executions.map((execution) => (
              <div
                key={execution.id}
                className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0"
              >
                <div className="space-y-1">
                  <p className="text-sm font-medium">{execution.workflowName}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatTimeAgo(execution.startedAt)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {execution.duration && (
                    <span className="text-xs text-muted-foreground">
                      {formatDuration(execution.duration)}
                    </span>
                  )}
                  <Badge variant={getStatusVariant(execution.status)}>
                    {execution.status}
                  </Badge>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
