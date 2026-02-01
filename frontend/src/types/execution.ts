export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused';

export interface ExecutionStep {
  id: string;
  stepId: string;
  stepName: string;
  status: ExecutionStatus;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: string;
  startedAt?: string;
  completedAt?: string;
  duration?: number;
}

export interface Execution {
  id: string;
  workflowId: string;
  workflowName: string;
  status: ExecutionStatus;
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: string;
  steps: ExecutionStep[];
  currentStepId?: string;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  triggeredBy: string;
  metadata?: Record<string, unknown>;
}

export interface StartExecutionRequest {
  workflowId: string;
  input?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface ExecutionLog {
  id: string;
  executionId: string;
  stepId?: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  data?: Record<string, unknown>;
  timestamp: string;
}

export interface ExecutionStats {
  total: number;
  completed: number;
  failed: number;
  running: number;
  pending: number;
  avgDuration: number;
  successRate: number;
}
