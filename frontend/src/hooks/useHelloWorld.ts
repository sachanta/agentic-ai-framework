/**
 * React Query hooks for Hello World app
 */
import { useQuery, useMutation } from '@tanstack/react-query';
import { helloWorldApi } from '@/api/apps';
import type { HelloWorldRequest, HelloWorldResponse } from '@/types/app';

// Query keys
export const helloWorldKeys = {
  all: ['hello-world'] as const,
  status: () => [...helloWorldKeys.all, 'status'] as const,
  agents: () => [...helloWorldKeys.all, 'agents'] as const,
};

/**
 * Hook to fetch Hello World status
 */
export function useHelloWorldStatus() {
  return useQuery({
    queryKey: helloWorldKeys.status(),
    queryFn: helloWorldApi.getStatus,
    staleTime: 30000,
  });
}

/**
 * Hook to fetch Hello World agents
 */
export function useHelloWorldAgents() {
  return useQuery({
    queryKey: helloWorldKeys.agents(),
    queryFn: helloWorldApi.getAgents,
  });
}

/**
 * Hook to execute Hello World greeting
 */
export function useExecuteHelloWorld() {
  return useMutation<HelloWorldResponse, Error, HelloWorldRequest>({
    mutationFn: helloWorldApi.execute,
  });
}
