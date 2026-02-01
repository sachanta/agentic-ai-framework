import { Link } from 'react-router-dom';
import { MoreVertical, Play, Copy, Archive, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatTimeAgo, formatNumber } from '@/utils/format';
import {
  useDeleteWorkflow,
  useDuplicateWorkflow,
  useExecuteWorkflow,
} from '@/hooks/useWorkflows';
import type { Workflow } from '@/types/workflow';

interface WorkflowCardProps {
  workflow: Workflow;
}

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  const deleteMutation = useDeleteWorkflow();
  const duplicateMutation = useDuplicateWorkflow();
  const executeMutation = useExecuteWorkflow();

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'draft':
        return 'secondary';
      case 'inactive':
        return 'outline';
      case 'archived':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const handleExecute = () => {
    executeMutation.mutate({ id: workflow.id });
  };

  const handleDuplicate = () => {
    duplicateMutation.mutate(workflow.id);
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this workflow?')) {
      deleteMutation.mutate(workflow.id);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div className="space-y-1">
          <Link to={`/workflows/${workflow.id}`}>
            <CardTitle className="hover:underline">{workflow.name}</CardTitle>
          </Link>
          <Badge variant={getStatusVariant(workflow.status)}>{workflow.status}</Badge>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleExecute} disabled={workflow.status !== 'active'}>
              <Play className="mr-2 h-4 w-4" />
              Execute
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleDuplicate}>
              <Copy className="mr-2 h-4 w-4" />
              Duplicate
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleDelete} className="text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">{workflow.description}</p>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Steps</p>
            <p className="font-medium">{workflow.steps.length}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Executions</p>
            <p className="font-medium">{formatNumber(workflow.executionCount)}</p>
          </div>
        </div>
        {workflow.lastExecutedAt && (
          <p className="text-xs text-muted-foreground mt-4">
            Last executed {formatTimeAgo(workflow.lastExecutedAt)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
