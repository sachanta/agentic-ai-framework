import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDateTime, formatDuration } from '@/utils/format';
import { useWorkflowExecutions } from '@/hooks/useWorkflows';

interface ExecutionHistoryProps {
  workflowId: string;
}

export function ExecutionHistory({ workflowId }: ExecutionHistoryProps) {
  const { data, isLoading } = useWorkflowExecutions(workflowId);

  const executions = data?.items ?? [];

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
        <CardTitle>Execution History</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : executions.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            No executions yet
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Triggered By</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {executions.map((execution) => (
                <TableRow key={execution.id}>
                  <TableCell>
                    <Link
                      to={`/executions/${execution.id}`}
                      className="font-mono text-sm hover:underline"
                    >
                      {execution.id.slice(0, 8)}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusVariant(execution.status)}>
                      {execution.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDateTime(execution.startedAt)}</TableCell>
                  <TableCell>
                    {execution.duration ? formatDuration(execution.duration) : '-'}
                  </TableCell>
                  <TableCell>{execution.triggeredBy}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
