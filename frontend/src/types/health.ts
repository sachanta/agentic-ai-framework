export type ServiceStatus = 'connected' | 'disconnected' | 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

export interface ServiceHealth {
  status: string;
  healthy: boolean;
  latency_ms?: number | null;
  version?: string | null;
  error?: string | null;
}

export interface SystemHealth {
  status: string;
  healthy: boolean;
  timestamp: number;
  services: {
    api: ServiceHealth;
    mongodb: ServiceHealth;
    weaviate: ServiceHealth;
  };
}

// Legacy types for components that haven't been updated
export interface DatabaseHealth {
  weaviate: ServiceHealth;
  mongodb: ServiceHealth;
}

export interface MemoryUsage {
  used: number;
  total: number;
  percentage: number;
  unit: string;
}

export interface QueueMetrics {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  total: number;
}

export interface HealthHistoryPoint {
  timestamp: string;
  memory: number;
  queueDepth: number;
  activeAgents: number;
  runningWorkflows: number;
}
