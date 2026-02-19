import apiClient from './client';
import type {
  StudioAgentDetail,
  StudioAgentsListResponse,
  StudioPlatformsListResponse,
} from '@/types/studio';

const BASE_PATH = '/api/v1/studio';

export const studioApi = {
  /** Discover all agents, optionally filtered by platform. */
  listAgents: async (platformId?: string): Promise<StudioAgentsListResponse> => {
    const params = platformId ? { platform_id: platformId } : undefined;
    const response = await apiClient.get<StudioAgentsListResponse>(
      `${BASE_PATH}/agents`,
      { params },
    );
    return response.data;
  },

  /** Get full detail for a single agent. */
  getAgent: async (platformId: string, agentName: string): Promise<StudioAgentDetail> => {
    const response = await apiClient.get<StudioAgentDetail>(
      `${BASE_PATH}/agents/${platformId}/${agentName}`,
    );
    return response.data;
  },

  /** List all platforms with agent counts. */
  listPlatforms: async (): Promise<StudioPlatformsListResponse> => {
    const response = await apiClient.get<StudioPlatformsListResponse>(
      `${BASE_PATH}/platforms`,
    );
    return response.data;
  },
};
