import apiClient from './client';
import type {
  StudioAgentDetail,
  StudioAgentsListResponse,
  StudioConfigUpdateRequest,
  StudioPlatformsListResponse,
  StudioPromptUpdateRequest,
  StudioProvidersListResponse,
  StudioTryRequest,
  StudioTryResponse,
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

  /** Update agent LLM config (session-only). */
  updateConfig: async (
    platformId: string,
    agentName: string,
    data: StudioConfigUpdateRequest,
  ): Promise<StudioAgentDetail> => {
    const response = await apiClient.patch<StudioAgentDetail>(
      `${BASE_PATH}/agents/${platformId}/${agentName}/config`,
      data,
    );
    return response.data;
  },

  /** Update agent system prompt (session-only). */
  updatePrompt: async (
    platformId: string,
    agentName: string,
    data: StudioPromptUpdateRequest,
  ): Promise<StudioAgentDetail> => {
    const response = await apiClient.put<StudioAgentDetail>(
      `${BASE_PATH}/agents/${platformId}/${agentName}/prompt`,
      data,
    );
    return response.data;
  },

  /** Execute agent with ad-hoc input. */
  tryAgent: async (
    platformId: string,
    agentName: string,
    data: StudioTryRequest,
  ): Promise<StudioTryResponse> => {
    const response = await apiClient.post<StudioTryResponse>(
      `${BASE_PATH}/agents/${platformId}/${agentName}/try`,
      data,
    );
    return response.data;
  },

  /** Reset agent overrides to defaults. */
  resetConfig: async (
    platformId: string,
    agentName: string,
  ): Promise<StudioAgentDetail> => {
    const response = await apiClient.delete<StudioAgentDetail>(
      `${BASE_PATH}/agents/${platformId}/${agentName}/config`,
    );
    return response.data;
  },

  /** List all LLM providers with model lists. */
  listProviders: async (): Promise<StudioProvidersListResponse> => {
    const response = await apiClient.get<StudioProvidersListResponse>(
      `${BASE_PATH}/providers`,
    );
    return response.data;
  },
};
