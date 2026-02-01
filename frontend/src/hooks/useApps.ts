/**
 * React Query hooks for apps/platforms
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { appsApi } from '@/api/apps';
import type { App, AppAgent, AppStatus } from '@/types/app';

// Query keys
export const appKeys = {
  all: ['apps'] as const,
  lists: () => [...appKeys.all, 'list'] as const,
  list: () => [...appKeys.lists()] as const,
  details: () => [...appKeys.all, 'detail'] as const,
  detail: (id: string) => [...appKeys.details(), id] as const,
  status: (id: string) => [...appKeys.all, 'status', id] as const,
  agents: (id: string) => [...appKeys.all, 'agents', id] as const,
};

/**
 * Hook to fetch all apps
 */
export function useApps() {
  return useQuery({
    queryKey: appKeys.list(),
    queryFn: appsApi.list,
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to fetch a single app
 */
export function useApp(appId: string) {
  return useQuery({
    queryKey: appKeys.detail(appId),
    queryFn: () => appsApi.get(appId),
    enabled: !!appId,
  });
}

/**
 * Hook to fetch app status
 */
export function useAppStatus(appId: string, options?: { polling?: boolean }) {
  return useQuery({
    queryKey: appKeys.status(appId),
    queryFn: () => appsApi.getStatus(appId),
    enabled: !!appId,
    refetchInterval: options?.polling ? 5000 : false,
  });
}

/**
 * Hook to fetch app agents
 */
export function useAppAgents(appId: string) {
  return useQuery({
    queryKey: appKeys.agents(appId),
    queryFn: () => appsApi.getAgents(appId),
    enabled: !!appId,
  });
}

/**
 * Hook to execute an app
 */
export function useExecuteApp(appId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Record<string, unknown>) => appsApi.execute(appId, input),
    onSuccess: () => {
      // Optionally invalidate related queries
      queryClient.invalidateQueries({ queryKey: appKeys.status(appId) });
    },
  });
}
