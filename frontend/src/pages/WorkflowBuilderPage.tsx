import { useState } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { Pencil, Play, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { WorkflowBuilder } from '@/components/workflows/WorkflowBuilder';
import { WorkflowForm } from '@/components/workflows/WorkflowForm';
import { ExecutionHistory } from '@/components/workflows/ExecutionHistory';
import { useWorkflow, useDeleteWorkflow, useExecuteWorkflow } from '@/hooks/useWorkflows';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '@/utils/constants';
import { Skeleton } from '@/components/ui/skeleton';

export function WorkflowBuilderPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isEditOpen, setIsEditOpen] = useState(false);
  const { data: workflow, isLoading, error } = useWorkflow(id!);
  const deleteMutation = useDeleteWorkflow();
  const executeMutation = useExecuteWorkflow();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-[600px]" />
      </div>
    );
  }

  if (error || !workflow) {
    return <Navigate to={ROUTES.WORKFLOWS} replace />;
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'draft':
        return 'secondary';
      case 'inactive':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this workflow?')) {
      await deleteMutation.mutateAsync(workflow.id);
      navigate('/workflows');
    }
  };

  const handleExecute = () => {
    executeMutation.mutate({ id: workflow.id });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{workflow.name}</h1>
          <p className="text-muted-foreground mt-1">{workflow.description}</p>
          <Badge variant={getStatusVariant(workflow.status)} className="mt-2">
            {workflow.status}
          </Badge>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleExecute}
            disabled={workflow.status !== 'active'}
          >
            <Play className="mr-2 h-4 w-4" />
            Execute
          </Button>
          <Button variant="outline" onClick={() => setIsEditOpen(true)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      <Tabs defaultValue="builder">
        <TabsList>
          <TabsTrigger value="builder">Builder</TabsTrigger>
          <TabsTrigger value="history">Execution History</TabsTrigger>
          <TabsTrigger value="variables">Variables</TabsTrigger>
        </TabsList>

        <TabsContent value="builder">
          <WorkflowBuilder workflow={workflow} />
        </TabsContent>

        <TabsContent value="history">
          <ExecutionHistory workflowId={workflow.id} />
        </TabsContent>

        <TabsContent value="variables">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Variables</CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(workflow.variables).length === 0 ? (
                <p className="text-muted-foreground">No variables defined</p>
              ) : (
                <pre className="p-4 bg-muted rounded-md overflow-auto">
                  {JSON.stringify(workflow.variables, null, 2)}
                </pre>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Workflow</DialogTitle>
          </DialogHeader>
          <WorkflowForm workflow={workflow} onSuccess={() => setIsEditOpen(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default WorkflowBuilderPage;
