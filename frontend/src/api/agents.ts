import apiClient from './client';
import type { Agent, CreateAgentRequest, UpdateAgentRequest, AgentExecution } from '@/types/agent';
import type { PaginatedResponse, QueryParams } from '@/types/common';

const BASE_PATH = '/api/v1/agents';

export const agentsApi = {
  list: async (params?: QueryParams): Promise<PaginatedResponse<Agent>> => {
    const response = await apiClient.get<PaginatedResponse<Agent>>(BASE_PATH, { params });
    return response.data;
  },

  get: async (id: string): Promise<Agent> => {
    const response = await apiClient.get<Agent>(`${BASE_PATH}/${id}`);
    return response.data;
  },

  create: async (data: CreateAgentRequest): Promise<Agent> => {
    const response = await apiClient.post<Agent>(BASE_PATH, data);
    return response.data;
  },

  update: async (id: string, data: UpdateAgentRequest): Promise<Agent> => {
    const response = await apiClient.patch<Agent>(`${BASE_PATH}/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`);
  },

  activate: async (id: string): Promise<Agent> => {
    const response = await apiClient.post<Agent>(`${BASE_PATH}/${id}/activate`);
    return response.data;
  },

  deactivate: async (id: string): Promise<Agent> => {
    const response = await apiClient.post<Agent>(`${BASE_PATH}/${id}/deactivate`);
    return response.data;
  },

  execute: async (id: string, input: Record<string, unknown>): Promise<AgentExecution> => {
    const response = await apiClient.post<AgentExecution>(`${BASE_PATH}/${id}/execute`, { input });
    return response.data;
  },

  getExecutions: async (id: string, params?: QueryParams): Promise<PaginatedResponse<AgentExecution>> => {
    const response = await apiClient.get<PaginatedResponse<AgentExecution>>(`${BASE_PATH}/${id}/executions`, { params });
    return response.data;
  },

  assignTools: async (id: string, toolIds: string[]): Promise<Agent> => {
    const response = await apiClient.post<Agent>(`${BASE_PATH}/${id}/tools`, { toolIds });
    return response.data;
  },

  removeTools: async (id: string, toolIds: string[]): Promise<Agent> => {
    const response = await apiClient.delete<Agent>(`${BASE_PATH}/${id}/tools`, { data: { toolIds } });
    return response.data;
  },
};
