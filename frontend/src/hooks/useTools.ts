import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toolsApi } from '@/api/tools';
import { notify } from '@/store/notificationStore';
import type { CreateToolRequest, UpdateToolRequest, ToolTestRequest } from '@/types/tool';
import type { QueryParams } from '@/types/common';

const QUERY_KEY = 'tools';

export function useTools(params?: QueryParams) {
  return useQuery({
    queryKey: [QUERY_KEY, params],
    queryFn: () => toolsApi.list(params),
  });
}

export function useTool(id: string) {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: () => toolsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateTool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateToolRequest) => toolsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Tool created successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to create tool', error.message);
    },
  });
}

export function useUpdateTool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateToolRequest }) => toolsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Tool updated successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to update tool', error.message);
    },
  });
}

export function useDeleteTool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => toolsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Tool deleted successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to delete tool', error.message);
    },
  });
}

export function useEnableTool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => toolsApi.enable(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Tool enabled');
    },
    onError: (error: Error) => {
      notify.error('Failed to enable tool', error.message);
    },
  });
}

export function useDisableTool() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => toolsApi.disable(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Tool disabled');
    },
    onError: (error: Error) => {
      notify.error('Failed to disable tool', error.message);
    },
  });
}

export function useTestTool() {
  return useMutation({
    mutationFn: (data: ToolTestRequest) => toolsApi.test(data),
    onSuccess: (result) => {
      if (result.success) {
        notify.success('Tool test passed');
      } else {
        notify.warning('Tool test failed', result.error);
      }
    },
    onError: (error: Error) => {
      notify.error('Failed to test tool', error.message);
    },
  });
}

export function useToolSchema(id: string) {
  return useQuery({
    queryKey: [QUERY_KEY, id, 'schema'],
    queryFn: () => toolsApi.getSchema(id),
    enabled: !!id,
  });
}
