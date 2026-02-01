import type { HealthStatus, ServiceHealth, MemoryUsage, QueueMetrics } from '@/types/health';

export const mockHealthStatus: HealthStatus = {
  status: 'healthy',
  timestamp: new Date().toISOString(),
  version: '1.0.0',
  uptime: 86400000,
};

export const mockServiceHealth: ServiceHealth[] = [
  {
    name: 'API Server',
    status: 'healthy',
    latency: 12,
    lastCheck: new Date().toISOString(),
  },
  {
    name: 'Weaviate',
    status: 'healthy',
    latency: 45,
    lastCheck: new Date().toISOString(),
    details: { cluster: 'default', nodes: 3 },
  },
  {
    name: 'MongoDB',
    status: 'healthy',
    latency: 23,
    lastCheck: new Date().toISOString(),
    details: { replicaSet: 'rs0', primary: 'mongodb-0' },
  },
  {
    name: 'Redis',
    status: 'healthy',
    latency: 5,
    lastCheck: new Date().toISOString(),
  },
  {
    name: 'Agent Executor',
    status: 'healthy',
    latency: 8,
    lastCheck: new Date().toISOString(),
    details: { activeAgents: 5, queuedTasks: 3 },
  },
  {
    name: 'Workflow Engine',
    status: 'healthy',
    latency: 15,
    lastCheck: new Date().toISOString(),
    details: { runningWorkflows: 2, pendingTriggers: 1 },
  },
];

export const mockMemoryUsage: MemoryUsage = {
  used: 2147483648, // 2GB
  total: 4294967296, // 4GB
  percentage: 50,
  history: Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
    used: 1800000000 + Math.random() * 500000000,
    total: 4294967296,
  })),
};

export const mockQueueMetrics: QueueMetrics = {
  pending: 8,
  processing: 4,
  completed: 1250,
  failed: 23,
  history: Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 3600000).toISOString(),
    pending: Math.floor(Math.random() * 15),
    processing: Math.floor(Math.random() * 8),
  })),
};

export function getRandomizedHealth(): ServiceHealth[] {
  return mockServiceHealth.map((service) => ({
    ...service,
    latency: service.latency + Math.floor(Math.random() * 10) - 5,
    lastCheck: new Date().toISOString(),
    status: Math.random() > 0.95 ? 'degraded' : 'healthy',
  }));
}

// Combined mock health object for handlers
export const mockHealth = {
  status: 'healthy',
  timestamp: new Date().toISOString(),
  version: '1.0.0',
  uptime: 86400000,
  services: mockServiceHealth,
  databases: {
    weaviate: {
      status: 'connected',
      latency: 45,
      cluster: 'default',
      nodes: 3,
    },
    mongodb: {
      status: 'connected',
      latency: 23,
      replicaSet: 'rs0',
      primary: 'mongodb-0',
    },
  },
  memory: {
    used: mockMemoryUsage.used,
    total: mockMemoryUsage.total,
    percentage: mockMemoryUsage.percentage,
  },
  queue: {
    pending: mockQueueMetrics.pending,
    processing: mockQueueMetrics.processing,
    completed: mockQueueMetrics.completed,
    failed: mockQueueMetrics.failed,
  },
};
