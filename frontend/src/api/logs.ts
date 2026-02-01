import apiClient from './client';
import type { PaginatedResponse, QueryParams } from '@/types/common';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  source: string;
  message: string;
  details?: Record<string, unknown>;
  user_id?: string;
  platform_id?: string;
  agent_id?: string;
  execution_id?: string;
  trace_id?: string;
  duration_ms?: number;
  error?: string;
}

export interface LogFilters {
  level?: string[];
  source?: string;
  startDate?: string;
  endDate?: string;
  search?: string;
  executionId?: string;
  agentId?: string;
  workflowId?: string;
}

const BASE_PATH = '/api/v1/logs';

export const logsApi = {
  list: async (params?: QueryParams & LogFilters): Promise<PaginatedResponse<LogEntry>> => {
    const response = await apiClient.get<PaginatedResponse<LogEntry>>(BASE_PATH, { params });
    return response.data;
  },

  get: async (id: string): Promise<LogEntry> => {
    const response = await apiClient.get<LogEntry>(`${BASE_PATH}/${id}`);
    return response.data;
  },

  getSources: async (): Promise<string[]> => {
    const response = await apiClient.get<{ sources: string[] }>(`${BASE_PATH}/sources`);
    return response.data.sources;
  },

  getLevels: async (): Promise<string[]> => {
    const response = await apiClient.get<{ levels: string[] }>(`${BASE_PATH}/levels`);
    return response.data.levels;
  },

  getStats: async (params?: { startDate?: string; endDate?: string }): Promise<{
    total: number;
    byLevel: Record<string, number>;
    bySource: Record<string, number>;
  }> => {
    const response = await apiClient.get(`${BASE_PATH}/stats`, { params });
    return response.data;
  },

  export: async (params?: LogFilters): Promise<Blob> => {
    const response = await apiClient.get(`${BASE_PATH}/export`, {
      params,
      responseType: 'blob',
    });
    return response.data;
  },

  clear: async (params?: { before?: string; level?: string }): Promise<{ deleted: number }> => {
    const response = await apiClient.delete(BASE_PATH, { params });
    return response.data;
  },
};
