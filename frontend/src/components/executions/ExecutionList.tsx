import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useExecutions } from '@/hooks/useExecutions';
import { formatDateTime, formatDuration } from '@/utils/format';
import { Skeleton } from '@/components/ui/skeleton';

export function ExecutionList() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const { data, isLoading, refetch } = useExecutions({
    search: search || undefined,
  });

  const executions = data?.items ?? [];
  const filteredExecutions =
    statusFilter === 'all'
      ? executions
      : executions.filter((e) => e.status === statusFilter);

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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative w-64">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search executions..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      ) : filteredExecutions.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No executions found</p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Workflow</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Started</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Triggered By</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredExecutions.map((execution) => (
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
                  <Link
                    to={`/workflows/${execution.workflowId}`}
                    className="hover:underline"
                  >
                    {execution.workflowName}
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
    </div>
  );
}
