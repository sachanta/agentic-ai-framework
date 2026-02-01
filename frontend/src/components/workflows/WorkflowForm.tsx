import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { workflowSchema, type WorkflowFormData } from '@/utils/validation';
import { useCreateWorkflow, useUpdateWorkflow } from '@/hooks/useWorkflows';
import type { Workflow } from '@/types/workflow';

interface WorkflowFormProps {
  workflow?: Workflow;
  onSuccess?: () => void;
}

export function WorkflowForm({ workflow, onSuccess }: WorkflowFormProps) {
  const navigate = useNavigate();
  const createMutation = useCreateWorkflow();
  const updateMutation = useUpdateWorkflow();
  const isEditing = !!workflow;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<WorkflowFormData>({
    resolver: zodResolver(workflowSchema),
    defaultValues: workflow
      ? {
          name: workflow.name,
          description: workflow.description,
          status: workflow.status,
        }
      : {
          status: 'draft',
        },
  });

  const onSubmit = async (data: WorkflowFormData) => {
    try {
      if (isEditing) {
        await updateMutation.mutateAsync({ id: workflow.id, data });
        onSuccess?.();
      } else {
        const newWorkflow = await createMutation.mutateAsync(data);
        navigate(`/workflows/${newWorkflow.id}`);
      }
    } catch {
      // Error handled by mutation
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          placeholder="My Workflow"
          {...register('name')}
          disabled={isPending}
        />
        {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          placeholder="Describe what this workflow does..."
          {...register('description')}
          disabled={isPending}
        />
        {errors.description && (
          <p className="text-sm text-destructive">{errors.description.message}</p>
        )}
      </div>

      <div className="flex justify-end gap-2">
        <Button type="submit" disabled={isPending}>
          {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isEditing ? 'Update Workflow' : 'Create Workflow'}
        </Button>
      </div>
    </form>
  );
}
