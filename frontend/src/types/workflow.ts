export type WorkflowStatus = 'draft' | 'active' | 'inactive' | 'archived';
export type StepType = 'agent' | 'tool' | 'condition' | 'loop' | 'parallel' | 'wait';

export interface WorkflowStepConfig {
  agentId?: string;
  toolId?: string;
  condition?: string;
  loopCount?: number;
  loopCondition?: string;
  waitDuration?: number;
  parallelSteps?: string[];
  inputMapping?: Record<string, string>;
  outputMapping?: Record<string, string>;
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: StepType;
  config: WorkflowStepConfig;
  position: { x: number; y: number };
  nextSteps: string[];
  onError?: 'stop' | 'continue' | 'retry';
  retryCount?: number;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  steps: WorkflowStep[];
  variables: Record<string, unknown>;
  triggers?: WorkflowTrigger[];
  createdAt: string;
  updatedAt: string;
  executionCount: number;
  lastExecutedAt?: string;
}

export interface WorkflowTrigger {
  id: string;
  type: 'schedule' | 'webhook' | 'event' | 'manual';
  config: Record<string, unknown>;
  enabled: boolean;
}

export interface CreateWorkflowRequest {
  name: string;
  description: string;
  steps?: WorkflowStep[];
  variables?: Record<string, unknown>;
  triggers?: WorkflowTrigger[];
}

export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  status?: WorkflowStatus;
  steps?: WorkflowStep[];
  variables?: Record<string, unknown>;
  triggers?: WorkflowTrigger[];
}
