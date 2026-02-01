export type ToolType = 'function' | 'api' | 'database' | 'file' | 'custom';

export interface ToolParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: unknown;
  enum?: string[];
}

export interface ToolSchema {
  name: string;
  description: string;
  parameters: ToolParameter[];
  returns?: {
    type: string;
    description: string;
  };
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  type: ToolType;
  schema: ToolSchema;
  enabled: boolean;
  version: string;
  createdAt: string;
  updatedAt: string;
  usageCount: number;
  avgExecutionTime?: number;
}

export interface CreateToolRequest {
  name: string;
  description: string;
  type: ToolType;
  schema: ToolSchema;
  enabled?: boolean;
}

export interface UpdateToolRequest {
  name?: string;
  description?: string;
  type?: ToolType;
  schema?: Partial<ToolSchema>;
  enabled?: boolean;
}

export interface ToolTestRequest {
  toolId: string;
  parameters: Record<string, unknown>;
}

export interface ToolTestResponse {
  success: boolean;
  result?: unknown;
  error?: string;
  executionTime: number;
}
