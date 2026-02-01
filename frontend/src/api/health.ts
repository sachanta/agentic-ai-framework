import apiClient from './client';
import type { SystemHealth, HealthHistoryPoint, ServiceHealth } from '@/types/health';

const BASE_PATH = '/api/v1/health';

export const healthApi = {
  getStatus: async (): Promise<SystemHealth> => {
    const response = await apiClient.get<SystemHealth>(BASE_PATH);
    return response.data;
  },

  getWeaviateStatus: async (): Promise<ServiceHealth> => {
    const response = await apiClient.get<ServiceHealth>(`${BASE_PATH}/weaviate`);
    return response.data;
  },

  getMongoDBStatus: async (): Promise<ServiceHealth> => {
    const response = await apiClient.get<ServiceHealth>(`${BASE_PATH}/mongodb`);
    return response.data;
  },

  getMemory: async (): Promise<{ used: number; total: number; percentage: number }> => {
    const response = await apiClient.get(`${BASE_PATH}/memory`);
    return response.data;
  },

  getQueue: async (): Promise<{ pending: number; processing: number; completed: number; failed: number }> => {
    const response = await apiClient.get(`${BASE_PATH}/queue`);
    return response.data;
  },

  getHistory: async (params?: { duration?: string }): Promise<HealthHistoryPoint[]> => {
    const response = await apiClient.get<HealthHistoryPoint[]>(`${BASE_PATH}/history`, { params });
    return response.data;
  },

  ping: async (): Promise<{ status: string; latency: number }> => {
    const start = Date.now();
    await apiClient.get(`${BASE_PATH}/ping`);
    return { status: 'ok', latency: Date.now() - start };
  },
};
