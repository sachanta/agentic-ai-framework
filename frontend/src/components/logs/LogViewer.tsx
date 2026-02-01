import { useState } from 'react';
import { Download, Trash2, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LogFilters } from './LogFilters';
import { LogEntry } from './LogEntry';
import { useLogs, useExportLogs, useClearLogs } from '@/hooks/useLogs';
import type { LogFilters as LogFiltersType } from '@/api/logs';

export function LogViewer() {
  const [filters, setFilters] = useState<LogFiltersType>({});
  const { data, isLoading, refetch } = useLogs(filters);
  const exportMutation = useExportLogs();
  const clearMutation = useClearLogs();

  const logs = data?.items ?? [];

  const handleExport = () => {
    exportMutation.mutate(filters);
  };

  const handleClear = () => {
    if (confirm('Are you sure you want to clear logs?')) {
      clearMutation.mutate({});
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <LogFilters filters={filters} onFiltersChange={setFilters} />
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleExport} disabled={exportMutation.isPending}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button variant="destructive" onClick={handleClear} disabled={clearMutation.isPending}>
            <Trash2 className="mr-2 h-4 w-4" />
            Clear
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Log Entries</CardTitle>
          <Badge variant="outline">{data?.total ?? 0} entries</Badge>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : logs.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No logs found
            </p>
          ) : (
            <ScrollArea className="h-[600px]">
              <div className="space-y-1">
                {logs.map((log) => (
                  <LogEntry key={log.id} log={log} />
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
