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
