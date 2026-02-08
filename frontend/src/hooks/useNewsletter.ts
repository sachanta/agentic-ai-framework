/**
 * React Query hooks for Newsletter platform
 */
import { useQuery, useMutation } from '@tanstack/react-query';
import { newsletterApi } from '@/api/apps';
import type {
  ResearchRequest,
  CustomResearchRequest,
  ResearchResponse,
  GenerateRequest,
  GenerateResponse,
} from '@/types/newsletter';

// Query keys
export const newsletterKeys = {
  all: ['newsletter'] as const,
  status: () => [...newsletterKeys.all, 'status'] as const,
  agents: () => [...newsletterKeys.all, 'agents'] as const,
  research: () => [...newsletterKeys.all, 'research'] as const,
  trending: (topics: string[]) => [...newsletterKeys.all, 'trending', topics] as const,
};

/**
 * Hook to fetch Newsletter platform status
 */
export function useNewsletterStatus() {
  return useQuery({
    queryKey: newsletterKeys.status(),
    queryFn: newsletterApi.getStatus,
    staleTime: 30000,
  });
}

/**
 * Hook to fetch Newsletter agents
 */
export function useNewsletterAgents() {
  return useQuery({
    queryKey: newsletterKeys.agents(),
    queryFn: newsletterApi.getAgents,
  });
}

/**
 * Hook to research content by topics
 */
export function useResearch() {
  return useMutation<ResearchResponse, Error, ResearchRequest>({
    mutationFn: newsletterApi.research,
  });
}

/**
 * Hook to research content using custom prompt
 */
export function useResearchCustom() {
  return useMutation<ResearchResponse, Error, CustomResearchRequest>({
    mutationFn: newsletterApi.researchCustom,
  });
}

/**
 * Hook to get trending content
 */
export function useTrending(topics: string[], maxResults: number = 10) {
  return useQuery({
    queryKey: newsletterKeys.trending(topics),
    queryFn: () => newsletterApi.getTrending(topics, maxResults),
    enabled: topics.length > 0,
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook to generate newsletter from selected articles
 */
export function useGenerateNewsletter() {
  return useMutation<GenerateResponse, Error, GenerateRequest>({
    mutationFn: newsletterApi.generate,
  });
}
