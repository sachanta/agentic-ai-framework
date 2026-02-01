import type { Workflow, WorkflowStep } from '@/types/workflow';

const researchSteps: WorkflowStep[] = [
  {
    id: 'step-1',
    name: 'Search Web',
    type: 'tool',
    toolId: 'tool-1',
    config: { maxResults: 20 },
    position: { x: 100, y: 100 },
  },
  {
    id: 'step-2',
    name: 'Query Vector DB',
    type: 'tool',
    toolId: 'tool-2',
    config: { collection: 'documents' },
    position: { x: 300, y: 100 },
  },
  {
    id: 'step-3',
    name: 'Analyze Results',
    type: 'agent',
    agentId: 'agent-1',
    config: {},
    position: { x: 200, y: 250 },
  },
  {
    id: 'step-4',
    name: 'Generate Report',
    type: 'agent',
    agentId: 'agent-1',
    config: {},
    position: { x: 200, y: 400 },
  },
];

const codeReviewSteps: WorkflowStep[] = [
  {
    id: 'step-1',
    name: 'Fetch Code',
    type: 'tool',
    toolId: 'tool-5',
    config: { operation: 'diff' },
    position: { x: 100, y: 100 },
  },
  {
    id: 'step-2',
    name: 'Static Analysis',
    type: 'tool',
    toolId: 'tool-4',
    config: {},
    position: { x: 300, y: 100 },
  },
  {
    id: 'step-3',
    name: 'Review Code',
    type: 'agent',
    agentId: 'agent-2',
    config: {},
    position: { x: 200, y: 250 },
  },
];

export const mockWorkflows: Workflow[] = [
  {
    id: 'workflow-1',
    name: 'Research Pipeline',
    description: 'Conducts comprehensive research on a given topic using multiple sources',
    status: 'active',
    trigger: {
      type: 'manual',
    },
    steps: researchSteps,
    connections: [
      { from: 'step-1', to: 'step-3' },
      { from: 'step-2', to: 'step-3' },
      { from: 'step-3', to: 'step-4' },
    ],
    createdAt: '2024-01-10T10:00:00Z',
    updatedAt: '2024-01-20T15:30:00Z',
    lastExecutedAt: '2024-01-22T09:15:00Z',
    executionCount: 45,
    successRate: 93.3,
  },
  {
    id: 'workflow-2',
    name: 'Code Review Automation',
    description: 'Automated code review pipeline with static analysis and AI review',
    status: 'active',
    trigger: {
      type: 'webhook',
      config: { event: 'pull_request' },
    },
    steps: codeReviewSteps,
    connections: [
      { from: 'step-1', to: 'step-2' },
      { from: 'step-2', to: 'step-3' },
    ],
    createdAt: '2024-01-12T14:00:00Z',
    updatedAt: '2024-01-21T11:00:00Z',
    lastExecutedAt: '2024-01-22T10:45:00Z',
    executionCount: 128,
    successRate: 96.1,
  },
  {
    id: 'workflow-3',
    name: 'Daily Data Sync',
    description: 'Synchronizes data between external sources and internal databases',
    status: 'active',
    trigger: {
      type: 'schedule',
      config: { cron: '0 2 * * *' },
    },
    steps: [
      {
        id: 'step-1',
        name: 'Fetch External Data',
        type: 'tool',
        toolId: 'tool-9',
        config: { method: 'GET' },
        position: { x: 100, y: 100 },
      },
      {
        id: 'step-2',
        name: 'Transform Data',
        type: 'tool',
        toolId: 'tool-6',
        config: { format: 'json' },
        position: { x: 250, y: 100 },
      },
      {
        id: 'step-3',
        name: 'Store in MongoDB',
        type: 'tool',
        toolId: 'tool-10',
        config: {},
        position: { x: 400, y: 100 },
      },
    ],
    connections: [
      { from: 'step-1', to: 'step-2' },
      { from: 'step-2', to: 'step-3' },
    ],
    createdAt: '2024-01-08T08:00:00Z',
    updatedAt: '2024-01-19T16:00:00Z',
    lastExecutedAt: '2024-01-22T02:00:00Z',
    executionCount: 14,
    successRate: 100,
  },
];
