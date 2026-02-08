/**
 * API service for apps/platforms
 */
import { apiClient } from './client';
import type {
  App,
  AppAgent,
  AppStatus,
  AppExecuteResponse,
  HelloWorldRequest,
  HelloWorldResponse,
} from '@/types/app';
import type {
  ResearchRequest,
  CustomResearchRequest,
  ResearchResponse,
  NewsletterStatus,
  NewsletterAgent,
  GenerateRequest,
  GenerateResponse,
} from '@/types/newsletter';

const BASE_PATH = '/api/v1/platforms';

interface PlatformListResponse {
  items: App[];
  total: number;
}

export const appsApi = {
  /**
   * List all available apps/platforms
   */
  list: async (): Promise<App[]> => {
    const response = await apiClient.get<PlatformListResponse>(BASE_PATH);
    return response.data.items;
  },

  /**
   * Get app details by ID
   */
  get: async (appId: string): Promise<App> => {
    const response = await apiClient.get<App>(`${BASE_PATH}/${appId}`);
    return response.data;
  },

  /**
   * Get app status
   */
  getStatus: async (appId: string): Promise<AppStatus> => {
    const response = await apiClient.get<AppStatus>(`${BASE_PATH}/${appId}/status`);
    return response.data;
  },

  /**
   * List agents in an app
   */
  getAgents: async (appId: string): Promise<AppAgent[]> => {
    const response = await apiClient.get<AppAgent[]>(`${BASE_PATH}/${appId}/agents`);
    return response.data;
  },

  /**
   * Execute an app
   */
  execute: async (appId: string, input: Record<string, unknown>): Promise<AppExecuteResponse> => {
    const response = await apiClient.post<AppExecuteResponse>(`${BASE_PATH}/${appId}/execute`, input);
    return response.data;
  },
};

interface PlatformExecuteResponse {
  success: boolean;
  result: HelloWorldResponse;
  execution_id: string | null;
  duration_ms: number;
}

/**
 * Hello World app specific API
 */
export const helloWorldApi = {
  /**
   * Get Hello World app status
   */
  getStatus: async (): Promise<AppStatus> => {
    const response = await apiClient.get<AppStatus>(`${BASE_PATH}/hello-world/status`);
    return response.data;
  },

  /**
   * List Hello World agents
   */
  getAgents: async (): Promise<AppAgent[]> => {
    const response = await apiClient.get<AppAgent[]>(`${BASE_PATH}/hello-world/agents`);
    return response.data;
  },

  /**
   * Execute Hello World greeting
   */
  execute: async (request: HelloWorldRequest): Promise<HelloWorldResponse> => {
    // Wrap request in { input: {...} } format expected by backend
    const response = await apiClient.post<PlatformExecuteResponse>(
      `${BASE_PATH}/hello-world/execute`,
      { input: request }
    );
    // Extract the greeting response from the result
    return response.data.result;
  },
};

// Longer timeout for LLM-powered research operations (3 minutes)
const RESEARCH_TIMEOUT = 180000;

/**
 * Newsletter Platform API
 */
export const newsletterApi = {
  /**
   * Get Newsletter platform status
   */
  getStatus: async (): Promise<NewsletterStatus> => {
    const response = await apiClient.get<NewsletterStatus>(`${BASE_PATH}/newsletter/status`);
    return response.data;
  },

  /**
   * List Newsletter agents
   */
  getAgents: async (): Promise<NewsletterAgent[]> => {
    const response = await apiClient.get<NewsletterAgent[]>(`${BASE_PATH}/newsletter/agents`);
    return response.data;
  },

  /**
   * Research content by topics
   */
  research: async (request: ResearchRequest): Promise<ResearchResponse> => {
    const response = await apiClient.post<ResearchResponse>(
      `${BASE_PATH}/newsletter/research`,
      request,
      { timeout: RESEARCH_TIMEOUT }
    );
    return response.data;
  },

  /**
   * Research content using custom prompt
   */
  researchCustom: async (request: CustomResearchRequest): Promise<ResearchResponse> => {
    const response = await apiClient.post<ResearchResponse>(
      `${BASE_PATH}/newsletter/research/custom`,
      request,
      { timeout: RESEARCH_TIMEOUT }
    );
    return response.data;
  },

  /**
   * Get trending content
   */
  getTrending: async (topics: string[], maxResults: number = 10): Promise<ResearchResponse> => {
    const response = await apiClient.get<ResearchResponse>(
      `${BASE_PATH}/newsletter/research/trending`,
      {
        params: {
          topics: topics.join(','),
          max_results: maxResults,
        },
        timeout: RESEARCH_TIMEOUT,
      }
    );
    return response.data;
  },

  /**
   * Generate newsletter from selected articles
   */
  generate: async (request: GenerateRequest): Promise<GenerateResponse> => {
    const response = await apiClient.post<GenerateResponse>(
      `${BASE_PATH}/newsletter/writing/generate`,
      request,
      { timeout: 300000 } // 5 minute timeout for generation
    );
    return response.data;
  },
};
