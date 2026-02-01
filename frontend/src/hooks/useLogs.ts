import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { logsApi, LogFilters } from '@/api/logs';
import { notify } from '@/store/notificationStore';
import type { QueryParams } from '@/types/common';

const QUERY_KEY = 'logs';

export function useLogs(params?: QueryParams & LogFilters) {
  return useQuery({
    queryKey: [QUERY_KEY, params],
    queryFn: () => logsApi.list(params),
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

export function useLog(id: string) {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: () => logsApi.get(id),
    enabled: !!id,
  });
}

export function useLogSources() {
  return useQuery({
    queryKey: [QUERY_KEY, 'sources'],
    queryFn: () => logsApi.getSources(),
  });
}

export function useLogStats(params?: { startDate?: string; endDate?: string }) {
  return useQuery({
    queryKey: [QUERY_KEY, 'stats', params],
    queryFn: () => logsApi.getStats(params),
  });
}

export function useExportLogs() {
  return useMutation({
    mutationFn: (params?: LogFilters) => logsApi.export(params),
    onSuccess: (blob) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `logs-${new Date().toISOString()}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      notify.success('Logs exported successfully');
    },
    onError: (error: Error) => {
      notify.error('Failed to export logs', error.message);
    },
  });
}

export function useClearLogs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params?: { before?: string; level?: string }) => logsApi.clear(params),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      notify.success(`Cleared ${result.deleted} log entries`);
    },
    onError: (error: Error) => {
      notify.error('Failed to clear logs', error.message);
    },
  });
}
