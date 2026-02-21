import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studioApi } from '@/api/studio';
import type {
  StudioConfigUpdateRequest,
  StudioPromptUpdateRequest,
  StudioTryRequest,
} from '@/types/studio';

const QUERY_KEY = 'studio';

/** Fetch all agents across all platforms, optionally filtered by platform. */
export function useStudioAgents(platformId?: string) {
  return useQuery({
    queryKey: [QUERY_KEY, 'agents', platformId],
    queryFn: () => studioApi.listAgents(platformId),
  });
}

/** Fetch full detail for a single agent. */
export function useStudioAgent(platformId: string, agentName: string) {
  return useQuery({
    queryKey: [QUERY_KEY, 'agents', platformId, agentName],
    queryFn: () => studioApi.getAgent(platformId, agentName),
    enabled: !!platformId && !!agentName,
  });
}

/** Fetch all platforms with agent counts. */
export function useStudioPlatforms() {
  return useQuery({
    queryKey: [QUERY_KEY, 'platforms'],
    queryFn: () => studioApi.listPlatforms(),
  });
}

/** Fetch all LLM providers with model lists. */
export function useStudioProviders() {
  return useQuery({
    queryKey: [QUERY_KEY, 'providers'],
    queryFn: () => studioApi.listProviders(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/** Mutation: update agent LLM config (session-only). */
export function useUpdateAgentConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      platformId,
      agentName,
      data,
    }: {
      platformId: string;
      agentName: string;
      data: StudioConfigUpdateRequest;
    }) => studioApi.updateConfig(platformId, agentName, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEY, 'agents', variables.platformId, variables.agentName],
      });
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEY, 'agents'],
        exact: false,
      });
    },
  });
}

/** Mutation: update agent system prompt (session-only). */
export function useUpdateAgentPrompt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      platformId,
      agentName,
      data,
    }: {
      platformId: string;
      agentName: string;
      data: StudioPromptUpdateRequest;
    }) => studioApi.updatePrompt(platformId, agentName, data),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(
        [QUERY_KEY, 'agents', variables.platformId, variables.agentName],
        data,
      );
    },
  });
}

/** Mutation: execute agent with ad-hoc input. */
export function useTryAgent() {
  return useMutation({
    mutationFn: ({
      platformId,
      agentName,
      data,
    }: {
      platformId: string;
      agentName: string;
      data: StudioTryRequest;
    }) => studioApi.tryAgent(platformId, agentName, data),
  });
}

/** Mutation: reset agent overrides to defaults. */
export function useResetAgentConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      platformId,
      agentName,
    }: {
      platformId: string;
      agentName: string;
    }) => studioApi.resetConfig(platformId, agentName),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEY, 'agents', variables.platformId, variables.agentName],
      });
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEY, 'agents'],
        exact: false,
      });
    },
  });
}
