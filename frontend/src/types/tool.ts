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

// ---------------------------------------------------------------------------
// Tools Studio types
// ---------------------------------------------------------------------------

export interface ToolStudioParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: unknown;
}

export interface ToolStudioSummary {
  tool_id: string;
  name: string;
  display_name: string;
  category: string;
  platform_id: string;
  service_class: string;
  description: string;
  parameter_count: number;
  status: string;
}

export interface ToolStudioDetail extends ToolStudioSummary {
  parameters: ToolStudioParameter[];
  returns?: string;
  requires: string[];
}

export interface ToolStudioListResponse {
  tools: ToolStudioSummary[];
  total: number;
  categories: string[];
}

export interface ToolStudioTryRequest {
  parameters: Record<string, unknown>;
}

export interface ToolStudioTryResponse {
  success: boolean;
  output?: unknown;
  error?: string;
  duration_ms: number;
  tool_id: string;
}

export interface ToolStudioCategory {
  name: string;
  count: number;
}
