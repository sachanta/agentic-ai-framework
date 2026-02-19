import { useQuery } from '@tanstack/react-query';
import { studioApi } from '@/api/studio';

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
