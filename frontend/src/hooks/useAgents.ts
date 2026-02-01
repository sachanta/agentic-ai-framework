import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentsApi } from '@/api/agents';
import { notify } from '@/store/notificationStore';
import type { CreateAgentRequest, UpdateAgentRequest } from '@/types/agent';
import type { QueryParams } from '@/types/common';

const QUERY_KEY = 'agents';

export function useAgents(params?: QueryParams) {
  return useQuery({
    queryKey: [QUERY_KEY, params],
    queryFn: () => agentsApi.list(params),
  });
}

export function useAgent(id: string) {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: () => agentsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAgentRequest) => agentsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Agent created successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to create agent', error.message);
    },
  });
}

export function useUpdateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateAgentRequest }) => agentsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Agent updated successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to update agent', error.message);
    },
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => agentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Agent deleted successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to delete agent', error.message);
    },
  });
}

export function useActivateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => agentsApi.activate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Agent activated');
    },
    onError: (error: Error) => {
      notify.error('Failed to activate agent', error.message);
    },
  });
}

export function useDeactivateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => agentsApi.deactivate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Agent deactivated');
    },
    onError: (error: Error) => {
      notify.error('Failed to deactivate agent', error.message);
    },
  });
}

export function useExecuteAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Record<string, unknown> }) =>
      agentsApi.execute(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      notify.success('Agent execution started');
    },
    onError: (error: Error) => {
      notify.error('Failed to execute agent', error.message);
    },
  });
}

export function useAgentExecutions(id: string, params?: QueryParams) {
  return useQuery({
    queryKey: [QUERY_KEY, id, 'executions', params],
    queryFn: () => agentsApi.getExecutions(id, params),
    enabled: !!id,
  });
}

export function useAssignTools() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, toolIds }: { id: string; toolIds: string[] }) =>
      agentsApi.assignTools(id, toolIds),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Tools assigned successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to assign tools', error.message);
    },
  });
}
