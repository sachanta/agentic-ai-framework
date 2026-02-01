import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useExecutionLogs } from '@/hooks/useExecutions';
import { formatDateTime } from '@/utils/format';

interface ExecutionLogsProps {
  executionId: string;
}

export function ExecutionLogs({ executionId }: ExecutionLogsProps) {
  const { data, isLoading } = useExecutionLogs(executionId);

  const logs = data?.items ?? [];

  const getLevelVariant = (level: string) => {
    switch (level) {
      case 'error':
        return 'destructive';
      case 'warn':
        return 'warning';
      case 'info':
        return 'default';
      default:
        return 'secondary';
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'text-red-500';
      case 'warn':
        return 'text-yellow-500';
      case 'info':
        return 'text-blue-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Execution Logs</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : logs.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            No logs available
          </p>
        ) : (
          <ScrollArea className="h-[400px]">
            <div className="space-y-2 font-mono text-sm">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="flex gap-2 p-2 hover:bg-muted rounded"
                >
                  <span className="text-muted-foreground whitespace-nowrap">
                    {formatDateTime(log.timestamp)}
                  </span>
                  <Badge variant={getLevelVariant(log.level)} className="h-5">
                    {log.level.toUpperCase()}
                  </Badge>
                  <span className={getLevelColor(log.level)}>{log.message}</span>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
