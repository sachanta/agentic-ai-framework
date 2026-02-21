import apiClient from './client';
import type {
  ToolStudioCategory,
  ToolStudioDetail,
  ToolStudioListResponse,
  ToolStudioTryRequest,
  ToolStudioTryResponse,
} from '@/types/tool';

const BASE_PATH = '/api/v1/tools-studio';

export const toolsStudioApi = {
  /** List all tools, optionally filtered by category. */
  listTools: async (category?: string): Promise<ToolStudioListResponse> => {
    const params = category ? { category } : undefined;
    const response = await apiClient.get<ToolStudioListResponse>(
      `${BASE_PATH}/tools`,
      { params },
    );
    return response.data;
  },

  /** Get full detail for a single tool. */
  getTool: async (toolId: string): Promise<ToolStudioDetail> => {
    const response = await apiClient.get<ToolStudioDetail>(
      `${BASE_PATH}/tools/${toolId}`,
    );
    return response.data;
  },

  /** Execute a tool with provided parameters. */
  tryTool: async (
    toolId: string,
    data: ToolStudioTryRequest,
  ): Promise<ToolStudioTryResponse> => {
    const response = await apiClient.post<ToolStudioTryResponse>(
      `${BASE_PATH}/tools/${toolId}/try`,
      data,
    );
    return response.data;
  },

  /** List all categories with tool counts. */
  listCategories: async (): Promise<ToolStudioCategory[]> => {
    const response = await apiClient.get<ToolStudioCategory[]>(
      `${BASE_PATH}/categories`,
    );
    return response.data;
  },
};
