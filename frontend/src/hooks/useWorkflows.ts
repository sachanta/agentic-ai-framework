import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowsApi } from '@/api/workflows';
import { notify } from '@/store/notificationStore';
import type { CreateWorkflowRequest, UpdateWorkflowRequest } from '@/types/workflow';
import type { QueryParams } from '@/types/common';

const QUERY_KEY = 'workflows';

export function useWorkflows(params?: QueryParams) {
  return useQuery({
    queryKey: [QUERY_KEY, params],
    queryFn: () => workflowsApi.list(params),
  });
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: () => workflowsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateWorkflowRequest) => workflowsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Workflow created successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to create workflow', error.message);
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateWorkflowRequest }) =>
      workflowsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Workflow updated successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to update workflow', error.message);
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => workflowsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Workflow deleted successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to delete workflow', error.message);
    },
  });
}

export function useActivateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => workflowsApi.activate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Workflow activated');
    },
    onError: (error: Error) => {
      notify.error('Failed to activate workflow', error.message);
    },
  });
}

export function useDeactivateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => workflowsApi.deactivate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Workflow deactivated');
    },
    onError: (error: Error) => {
      notify.error('Failed to deactivate workflow', error.message);
    },
  });
}

export function useDuplicateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => workflowsApi.duplicate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Workflow duplicated');
    },
    onError: (error: Error) => {
      notify.error('Failed to duplicate workflow', error.message);
    },
  });
}

export function useExecuteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input?: Record<string, unknown> }) =>
      workflowsApi.execute(id, { input }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      notify.success('Workflow execution started');
    },
    onError: (error: Error) => {
      notify.error('Failed to execute workflow', error.message);
    },
  });
}

export function useWorkflowExecutions(id: string, params?: QueryParams) {
  return useQuery({
    queryKey: [QUERY_KEY, id, 'executions', params],
    queryFn: () => workflowsApi.getExecutions(id, params),
    enabled: !!id,
  });
}

export function useValidateWorkflow() {
  return useMutation({
    mutationFn: (id: string) => workflowsApi.validateSteps(id),
    onSuccess: (result) => {
      if (result.valid) {
        notify.success('Workflow is valid');
      } else {
        notify.warning('Workflow has validation errors', result.errors.join(', '));
      }
    },
    onError: (error: Error) => {
      notify.error('Failed to validate workflow', error.message);
    },
  });
}
