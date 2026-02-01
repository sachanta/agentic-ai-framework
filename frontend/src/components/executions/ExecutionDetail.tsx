import { Link } from 'react-router-dom';
import { StopCircle, Pause, Play, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ExecutionProgress } from './ExecutionProgress';
import { ExecutionLogs } from './ExecutionLogs';
import { formatDateTime, formatDuration } from '@/utils/format';
import {
  useCancelExecution,
  usePauseExecution,
  useResumeExecution,
  useRetryExecution,
} from '@/hooks/useExecutions';
import type { Execution } from '@/types/execution';

interface ExecutionDetailProps {
  execution: Execution;
}

export function ExecutionDetail({ execution }: ExecutionDetailProps) {
  const cancelMutation = useCancelExecution();
  const pauseMutation = usePauseExecution();
  const resumeMutation = useResumeExecution();
  const retryMutation = useRetryExecution();

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
      case 'paused':
        return 'warning';
      default:
        return 'outline';
    }
  };

  const isRunning = execution.status === 'running';
  const isPaused = execution.status === 'paused';
  const isFailed = execution.status === 'failed';

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold font-mono">{execution.id.slice(0, 8)}</h1>
          <p className="text-muted-foreground mt-1">
            Workflow:{' '}
            <Link to={`/workflows/${execution.workflowId}`} className="hover:underline">
              {execution.workflowName}
            </Link>
          </p>
          <Badge variant={getStatusVariant(execution.status)} className="mt-2">
            {execution.status}
          </Badge>
        </div>
        <div className="flex gap-2">
          {isRunning && (
            <>
              <Button variant="outline" onClick={() => pauseMutation.mutate(execution.id)}>
                <Pause className="mr-2 h-4 w-4" />
                Pause
              </Button>
              <Button variant="destructive" onClick={() => cancelMutation.mutate(execution.id)}>
                <StopCircle className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            </>
          )}
          {isPaused && (
            <Button variant="outline" onClick={() => resumeMutation.mutate(execution.id)}>
              <Play className="mr-2 h-4 w-4" />
              Resume
            </Button>
          )}
          {isFailed && (
            <Button variant="outline" onClick={() => retryMutation.mutate(execution.id)}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Started</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{formatDateTime(execution.startedAt)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              {execution.completedAt ? formatDateTime(execution.completedAt) : '-'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              {execution.duration ? formatDuration(execution.duration) : '-'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Triggered By</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{execution.triggeredBy}</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="progress">
        <TabsList>
          <TabsTrigger value="progress">Progress</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="input">Input</TabsTrigger>
          <TabsTrigger value="output">Output</TabsTrigger>
        </TabsList>

        <TabsContent value="progress">
          <ExecutionProgress execution={execution} />
        </TabsContent>

        <TabsContent value="logs">
          <ExecutionLogs executionId={execution.id} />
        </TabsContent>

        <TabsContent value="input">
          <Card>
            <CardHeader>
              <CardTitle>Input</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="p-4 bg-muted rounded-md overflow-auto text-sm">
                {JSON.stringify(execution.input, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="output">
          <Card>
            <CardHeader>
              <CardTitle>Output</CardTitle>
            </CardHeader>
            <CardContent>
              {execution.output ? (
                <pre className="p-4 bg-muted rounded-md overflow-auto text-sm">
                  {JSON.stringify(execution.output, null, 2)}
                </pre>
              ) : execution.error ? (
                <div className="p-4 bg-destructive/10 rounded-md">
                  <p className="text-destructive">{execution.error}</p>
                </div>
              ) : (
                <p className="text-muted-foreground">No output yet</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
