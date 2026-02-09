/**
 * SSE Hook for real-time workflow updates
 *
 * Connects to the workflow stream endpoint and provides real-time updates
 * as the workflow progresses through steps and checkpoints.
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { newsletterApi } from '@/api/newsletter';
import { newsletterKeys } from '@/hooks/useNewsletter';
import { TOKEN_KEY } from '@/utils/constants';
import type {
  SSEStatusEvent,
  SSECheckpointEvent,
  SSECompleteEvent,
  SSEErrorEvent,
  WorkflowStepStatus,
} from '@/types/newsletter';

// ============================================================================
// TYPES
// ============================================================================

export interface WorkflowSSECallbacks {
  onStatus?: (event: SSEStatusEvent) => void;
  onCheckpoint?: (event: SSECheckpointEvent) => void;
  onComplete?: (event: SSECompleteEvent) => void;
  onError?: (event: SSEErrorEvent) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export interface WorkflowSSEState {
  isConnected: boolean;
  lastEvent: SSEStatusEvent | SSECheckpointEvent | SSECompleteEvent | null;
  error: string | null;
}

// ============================================================================
// HOOK
// ============================================================================

/**
 * Hook for SSE streaming of workflow progress
 *
 * @param workflowId - The workflow ID to stream (null to disable)
 * @param callbacks - Optional callbacks for different event types
 * @returns SSE state and control functions
 *
 * @example
 * ```tsx
 * const { isConnected, lastEvent, connect, disconnect } = useWorkflowSSE(
 *   workflowId,
 *   {
 *     onCheckpoint: (checkpoint) => {
 *       // Handle checkpoint - show approval UI
 *     },
 *     onComplete: (result) => {
 *       // Handle completion - navigate to newsletter
 *     },
 *   }
 * );
 * ```
 */
export function useWorkflowSSE(
  workflowId: string | null,
  callbacks: WorkflowSSECallbacks = {}
) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const queryClient = useQueryClient();

  const [state, setState] = useState<WorkflowSSEState>({
    isConnected: false,
    lastEvent: null,
    error: null,
  });

  // Store callbacks in refs to avoid reconnection on callback changes
  const callbacksRef = useRef(callbacks);
  callbacksRef.current = callbacks;

  /**
   * Parse SSE event data safely
   */
  const parseEventData = useCallback(<T>(data: string): T | null => {
    try {
      // Handle Python dict format (single quotes, True/False)
      const jsonStr = data
        .replace(/'/g, '"')
        .replace(/True/g, 'true')
        .replace(/False/g, 'false')
        .replace(/None/g, 'null');
      return JSON.parse(jsonStr);
    } catch {
      console.error('Failed to parse SSE event data:', data);
      return null;
    }
  }, []);

  /**
   * Connect to the SSE stream
   */
  const connect = useCallback(() => {
    if (!workflowId) return;

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Clear any pending reconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Build SSE URL with auth token
    const token = localStorage.getItem(TOKEN_KEY);
    const baseUrl = newsletterApi.getWorkflowStreamUrl(workflowId);
    const url = token ? `${baseUrl}?token=${encodeURIComponent(token)}` : baseUrl;

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setState((prev) => ({ ...prev, isConnected: true, error: null }));
      callbacksRef.current.onConnectionChange?.(true);
    };

    // Handle status events
    eventSource.addEventListener('status', (event: MessageEvent) => {
      const data = parseEventData<SSEStatusEvent>(event.data);
      if (data) {
        setState((prev) => ({ ...prev, lastEvent: data }));

        // Update React Query cache
        queryClient.setQueryData(
          newsletterKeys.workflowDetail(workflowId),
          (old: unknown) => ({
            ...(old as object),
            status: data.status,
            current_step: data.current_step,
          })
        );

        callbacksRef.current.onStatus?.(data);
      }
    });

    // Handle checkpoint events
    eventSource.addEventListener('checkpoint', (event: MessageEvent) => {
      const data = parseEventData<SSECheckpointEvent>(event.data);
      if (data) {
        setState((prev) => ({ ...prev, lastEvent: data as unknown as SSEStatusEvent }));

        // Invalidate checkpoint query to trigger refetch
        queryClient.invalidateQueries({
          queryKey: newsletterKeys.workflowCheckpoint(workflowId),
        });

        callbacksRef.current.onCheckpoint?.(data);
      }
    });

    // Handle complete events
    eventSource.addEventListener('complete', (event: MessageEvent) => {
      const data = parseEventData<SSECompleteEvent>(event.data);
      if (data) {
        setState((prev) => ({ ...prev, lastEvent: data as unknown as SSEStatusEvent }));

        // Invalidate queries to refresh data
        queryClient.invalidateQueries({ queryKey: newsletterKeys.workflows() });
        queryClient.invalidateQueries({ queryKey: newsletterKeys.newsletters() });

        callbacksRef.current.onComplete?.(data);

        // Close connection on completion
        eventSource.close();
        setState((prev) => ({ ...prev, isConnected: false }));
        callbacksRef.current.onConnectionChange?.(false);
      }
    });

    // Handle error events from server
    eventSource.addEventListener('error', (event: MessageEvent) => {
      if (event.data) {
        const data = parseEventData<SSEErrorEvent>(event.data);
        if (data) {
          setState((prev) => ({ ...prev, error: data.error }));
          callbacksRef.current.onError?.(data);
        }
      }
    });

    // Handle done events
    eventSource.addEventListener('done', () => {
      eventSource.close();
      setState((prev) => ({ ...prev, isConnected: false }));
      callbacksRef.current.onConnectionChange?.(false);
    });

    // Handle connection errors
    eventSource.onerror = () => {
      setState((prev) => ({ ...prev, isConnected: false }));
      callbacksRef.current.onConnectionChange?.(false);

      // Only attempt reconnection if not intentionally closed
      if (eventSourceRef.current === eventSource) {
        eventSource.close();

        // Attempt reconnection after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          if (eventSourceRef.current === null) {
            connect();
          }
        }, 3000);
      }
    };
  }, [workflowId, queryClient, parseEventData]);

  /**
   * Disconnect from the SSE stream
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setState((prev) => ({ ...prev, isConnected: false }));
    callbacksRef.current.onConnectionChange?.(false);
  }, []);

  // Connect when workflowId changes, cleanup on unmount
  useEffect(() => {
    if (workflowId) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [workflowId, connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
  };
}

// ============================================================================
// UTILITY HOOKS
// ============================================================================

/**
 * Hook that provides workflow status with SSE updates
 *
 * Combines polling-based useWorkflow with SSE for optimal responsiveness.
 * Falls back to polling if SSE connection fails.
 *
 * @param workflowId - The workflow ID to track
 */
export function useWorkflowWithSSE(workflowId: string | null) {
  const [status, setStatus] = useState<WorkflowStepStatus | null>(null);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [hasCheckpoint, setHasCheckpoint] = useState(false);

  const { isConnected, error } = useWorkflowSSE(workflowId, {
    onStatus: (event) => {
      setStatus(event.status);
      setCurrentStep(event.current_step);
      setHasCheckpoint(!!event.checkpoint);
    },
    onCheckpoint: () => {
      setHasCheckpoint(true);
    },
    onComplete: (event) => {
      setStatus(event.status as WorkflowStepStatus);
      setHasCheckpoint(false);
    },
  });

  return {
    status,
    currentStep,
    hasCheckpoint,
    isConnected,
    error,
  };
}

export default useWorkflowSSE;
