import { useQuery, useMutation } from '@tanstack/react-query';
import { toolsStudioApi } from '@/api/toolsStudio';
import type { ToolStudioTryRequest } from '@/types/tool';

const QUERY_KEY = 'tools-studio';

/** Fetch all tools, optionally filtered by category. */
export function useToolsStudioList(category?: string) {
  return useQuery({
    queryKey: [QUERY_KEY, 'tools', category],
    queryFn: () => toolsStudioApi.listTools(category),
  });
}

/** Fetch full detail for a single tool. */
export function useToolsStudioDetail(toolId: string) {
  return useQuery({
    queryKey: [QUERY_KEY, 'tools', toolId],
    queryFn: () => toolsStudioApi.getTool(toolId),
    enabled: !!toolId,
  });
}

/** Fetch all categories with counts. */
export function useToolsStudioCategories() {
  return useQuery({
    queryKey: [QUERY_KEY, 'categories'],
    queryFn: () => toolsStudioApi.listCategories(),
    staleTime: 1000 * 60 * 5,
  });
}

/** Mutation: execute a tool with parameters. */
export function useTryTool() {
  return useMutation({
    mutationFn: ({
      toolId,
      data,
    }: {
      toolId: string;
      data: ToolStudioTryRequest;
    }) => toolsStudioApi.tryTool(toolId, data),
  });
}
