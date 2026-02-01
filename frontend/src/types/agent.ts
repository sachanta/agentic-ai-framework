export type AgentStatus = 'active' | 'inactive' | 'error' | 'initializing';

export interface AgentConfig {
  model: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
  timeout?: number;
  retryAttempts?: number;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: AgentStatus;
  config: AgentConfig;
  tools: string[];
  createdAt: string;
  updatedAt: string;
  lastExecutedAt?: string;
  executionCount: number;
  successRate: number;
}

export interface CreateAgentRequest {
  name: string;
  description: string;
  config: AgentConfig;
  tools?: string[];
}

export interface UpdateAgentRequest {
  name?: string;
  description?: string;
  config?: Partial<AgentConfig>;
  tools?: string[];
  status?: AgentStatus;
}

export interface AgentExecution {
  id: string;
  agentId: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: string;
  startedAt: string;
  completedAt?: string;
  duration?: number;
}
