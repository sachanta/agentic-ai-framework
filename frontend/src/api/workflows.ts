import apiClient from './client';
import type { Workflow, CreateWorkflowRequest, UpdateWorkflowRequest } from '@/types/workflow';
import type { Execution, StartExecutionRequest } from '@/types/execution';
import type { PaginatedResponse, QueryParams } from '@/types/common';

const BASE_PATH = '/api/v1/workflows';

export const workflowsApi = {
  list: async (params?: QueryParams): Promise<PaginatedResponse<Workflow>> => {
    const response = await apiClient.get<PaginatedResponse<Workflow>>(BASE_PATH, { params });
    return response.data;
  },

  get: async (id: string): Promise<Workflow> => {
    const response = await apiClient.get<Workflow>(`${BASE_PATH}/${id}`);
    return response.data;
  },

  create: async (data: CreateWorkflowRequest): Promise<Workflow> => {
    const response = await apiClient.post<Workflow>(BASE_PATH, data);
    return response.data;
  },

  update: async (id: string, data: UpdateWorkflowRequest): Promise<Workflow> => {
    const response = await apiClient.patch<Workflow>(`${BASE_PATH}/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`);
  },

  activate: async (id: string): Promise<Workflow> => {
    const response = await apiClient.post<Workflow>(`${BASE_PATH}/${id}/activate`);
    return response.data;
  },

  deactivate: async (id: string): Promise<Workflow> => {
    const response = await apiClient.post<Workflow>(`${BASE_PATH}/${id}/deactivate`);
    return response.data;
  },

  archive: async (id: string): Promise<Workflow> => {
    const response = await apiClient.post<Workflow>(`${BASE_PATH}/${id}/archive`);
    return response.data;
  },

  duplicate: async (id: string): Promise<Workflow> => {
    const response = await apiClient.post<Workflow>(`${BASE_PATH}/${id}/duplicate`);
    return response.data;
  },

  execute: async (id: string, request?: Omit<StartExecutionRequest, 'workflowId'>): Promise<Execution> => {
    const response = await apiClient.post<Execution>(`${BASE_PATH}/${id}/execute`, request);
    return response.data;
  },

  getExecutions: async (id: string, params?: QueryParams): Promise<PaginatedResponse<Execution>> => {
    const response = await apiClient.get<PaginatedResponse<Execution>>(`${BASE_PATH}/${id}/executions`, { params });
    return response.data;
  },

  validateSteps: async (id: string): Promise<{ valid: boolean; errors: string[] }> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/validate`);
    return response.data;
  },
};
