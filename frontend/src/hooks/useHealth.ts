import { useQuery } from '@tanstack/react-query';
import { healthApi } from '@/api/health';
import { HEALTH_REFRESH_INTERVAL } from '@/utils/constants';

const QUERY_KEY = 'health';

export function useHealth(enabled = true) {
  return useQuery({
    queryKey: [QUERY_KEY],
    queryFn: () => healthApi.getStatus(),
    refetchInterval: HEALTH_REFRESH_INTERVAL,
    enabled,
  });
}

export function useWeaviateHealth(enabled = true) {
  return useQuery({
    queryKey: [QUERY_KEY, 'weaviate'],
    queryFn: () => healthApi.getWeaviateStatus(),
    refetchInterval: HEALTH_REFRESH_INTERVAL,
    enabled,
  });
}

export function useMongoDBHealth(enabled = true) {
  return useQuery({
    queryKey: [QUERY_KEY, 'mongodb'],
    queryFn: () => healthApi.getMongoDBStatus(),
    refetchInterval: HEALTH_REFRESH_INTERVAL,
    enabled,
  });
}

export function useMemoryUsage(enabled = true) {
  return useQuery({
    queryKey: [QUERY_KEY, 'memory'],
    queryFn: () => healthApi.getMemory(),
    refetchInterval: HEALTH_REFRESH_INTERVAL,
    enabled,
  });
}

export function useQueueMetrics(enabled = true) {
  return useQuery({
    queryKey: [QUERY_KEY, 'queue'],
    queryFn: () => healthApi.getQueue(),
    refetchInterval: HEALTH_REFRESH_INTERVAL,
    enabled,
  });
}

export function useHealthHistory(duration?: string) {
  return useQuery({
    queryKey: [QUERY_KEY, 'history', duration],
    queryFn: () => healthApi.getHistory({ duration }),
  });
}

export function usePing() {
  return useQuery({
    queryKey: [QUERY_KEY, 'ping'],
    queryFn: () => healthApi.ping(),
    refetchInterval: 5000, // Ping every 5 seconds
  });
}
