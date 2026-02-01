import apiClient from './client';
import type { Tool, CreateToolRequest, UpdateToolRequest, ToolTestRequest, ToolTestResponse } from '@/types/tool';
import type { PaginatedResponse, QueryParams } from '@/types/common';

const BASE_PATH = '/api/v1/tools';

export const toolsApi = {
  list: async (params?: QueryParams): Promise<PaginatedResponse<Tool>> => {
    const response = await apiClient.get<PaginatedResponse<Tool>>(BASE_PATH, { params });
    return response.data;
  },

  get: async (id: string): Promise<Tool> => {
    const response = await apiClient.get<Tool>(`${BASE_PATH}/${id}`);
    return response.data;
  },

  create: async (data: CreateToolRequest): Promise<Tool> => {
    const response = await apiClient.post<Tool>(BASE_PATH, data);
    return response.data;
  },

  update: async (id: string, data: UpdateToolRequest): Promise<Tool> => {
    const response = await apiClient.patch<Tool>(`${BASE_PATH}/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`);
  },

  enable: async (id: string): Promise<Tool> => {
    const response = await apiClient.post<Tool>(`${BASE_PATH}/${id}/enable`);
    return response.data;
  },

  disable: async (id: string): Promise<Tool> => {
    const response = await apiClient.post<Tool>(`${BASE_PATH}/${id}/disable`);
    return response.data;
  },

  test: async (data: ToolTestRequest): Promise<ToolTestResponse> => {
    const response = await apiClient.post<ToolTestResponse>(`${BASE_PATH}/${data.toolId}/test`, {
      parameters: data.parameters,
    });
    return response.data;
  },

  getSchema: async (id: string): Promise<Record<string, unknown>> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}/schema`);
    return response.data;
  },
};
