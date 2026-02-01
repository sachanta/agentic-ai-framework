import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { executionsApi } from '@/api/executions';
import { notify } from '@/store/notificationStore';
import type { StartExecutionRequest } from '@/types/execution';
import type { QueryParams } from '@/types/common';

const QUERY_KEY = 'executions';

export function useExecutions(params?: QueryParams) {
  return useQuery({
    queryKey: [QUERY_KEY, params],
    queryFn: () => executionsApi.list(params),
  });
}

export function useExecution(id: string) {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: () => executionsApi.get(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Refetch every 2 seconds if execution is running
      if (data?.status === 'running' || data?.status === 'pending') {
        return 2000;
      }
      return false;
    },
  });
}

export function useStartExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: StartExecutionRequest) => executionsApi.start(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Execution started');
    },
    onError: (error: Error) => {
      notify.error('Failed to start execution', error.message);
    },
  });
}

export function useCancelExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => executionsApi.cancel(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Execution cancelled');
    },
    onError: (error: Error) => {
      notify.error('Failed to cancel execution', error.message);
    },
  });
}

export function usePauseExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => executionsApi.pause(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Execution paused');
    },
    onError: (error: Error) => {
      notify.error('Failed to pause execution', error.message);
    },
  });
}

export function useResumeExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => executionsApi.resume(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
      notify.success('Execution resumed');
    },
    onError: (error: Error) => {
      notify.error('Failed to resume execution', error.message);
    },
  });
}

export function useRetryExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => executionsApi.retry(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Execution retried');
    },
    onError: (error: Error) => {
      notify.error('Failed to retry execution', error.message);
    },
  });
}

export function useDeleteExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => executionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success('Execution deleted');
    },
    onError: (error: Error) => {
      notify.error('Failed to delete execution', error.message);
    },
  });
}

export function useExecutionLogs(id: string, params?: QueryParams) {
  return useQuery({
    queryKey: [QUERY_KEY, id, 'logs', params],
    queryFn: () => executionsApi.getLogs(id, params),
    enabled: !!id,
  });
}

export function useExecutionStats(params?: { startDate?: string; endDate?: string }) {
  return useQuery({
    queryKey: [QUERY_KEY, 'stats', params],
    queryFn: () => executionsApi.getStats(params),
  });
}
