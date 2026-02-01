import apiClient from './client';
import type { Execution, ExecutionLog, ExecutionStats, StartExecutionRequest } from '@/types/execution';
import type { PaginatedResponse, QueryParams } from '@/types/common';

const BASE_PATH = '/api/v1/executions';

export const executionsApi = {
  list: async (params?: QueryParams): Promise<PaginatedResponse<Execution>> => {
    const response = await apiClient.get<PaginatedResponse<Execution>>(BASE_PATH, { params });
    return response.data;
  },

  get: async (id: string): Promise<Execution> => {
    const response = await apiClient.get<Execution>(`${BASE_PATH}/${id}`);
    return response.data;
  },

  start: async (data: StartExecutionRequest): Promise<Execution> => {
    const response = await apiClient.post<Execution>(BASE_PATH, data);
    return response.data;
  },

  cancel: async (id: string): Promise<Execution> => {
    const response = await apiClient.post<Execution>(`${BASE_PATH}/${id}/cancel`);
    return response.data;
  },

  pause: async (id: string): Promise<Execution> => {
    const response = await apiClient.post<Execution>(`${BASE_PATH}/${id}/pause`);
    return response.data;
  },

  resume: async (id: string): Promise<Execution> => {
    const response = await apiClient.post<Execution>(`${BASE_PATH}/${id}/resume`);
    return response.data;
  },

  retry: async (id: string): Promise<Execution> => {
    const response = await apiClient.post<Execution>(`${BASE_PATH}/${id}/retry`);
    return response.data;
  },

  getLogs: async (id: string, params?: QueryParams): Promise<PaginatedResponse<ExecutionLog>> => {
    const response = await apiClient.get<PaginatedResponse<ExecutionLog>>(`${BASE_PATH}/${id}/logs`, { params });
    return response.data;
  },

  getStats: async (params?: { startDate?: string; endDate?: string }): Promise<ExecutionStats> => {
    const response = await apiClient.get<ExecutionStats>(`${BASE_PATH}/stats`, { params });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`);
  },

  bulkDelete: async (ids: string[]): Promise<void> => {
    await apiClient.delete(BASE_PATH, { data: { ids } });
  },
};
