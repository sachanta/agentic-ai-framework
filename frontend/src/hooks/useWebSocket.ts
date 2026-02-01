import { useEffect, useRef, useState, useCallback } from 'react';
import { WS_URL, LOG_STREAM_RECONNECT_INTERVAL } from '@/utils/constants';
import { useAuthStore } from '@/store/authStore';

interface WebSocketOptions {
  url: string;
  onMessage?: (data: unknown) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnect?: boolean;
  reconnectInterval?: number;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
}

export function useWebSocket(options: WebSocketOptions) {
  const {
    url,
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnect = true,
    reconnectInterval = LOG_STREAM_RECONNECT_INTERVAL,
  } = options;

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { token } = useAuthStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setState((prev) => ({ ...prev, isConnecting: true, error: null }));

    const wsUrl = new URL(url, WS_URL);
    if (token) {
      wsUrl.searchParams.set('token', token);
    }

    const ws = new WebSocket(wsUrl.toString());

    ws.onopen = () => {
      setState({ isConnected: true, isConnecting: false, error: null });
      onOpen?.();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch {
        onMessage?.(event.data);
      }
    };

    ws.onerror = (event) => {
      setState((prev) => ({ ...prev, error: 'WebSocket error' }));
      onError?.(event);
    };

    ws.onclose = () => {
      setState({ isConnected: false, isConnecting: false, error: null });
      onClose?.();

      if (reconnect) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      }
    };

    wsRef.current = ws;
  }, [url, token, onMessage, onError, onOpen, onClose, reconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState({ isConnected: false, isConnecting: false, error: null });
  }, []);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    send,
  };
}

export function useLogStream(onLog: (log: unknown) => void) {
  return useWebSocket({
    url: '/ws/logs',
    onMessage: onLog,
    reconnect: true,
  });
}

export function useExecutionStream(executionId: string, onUpdate: (data: unknown) => void) {
  return useWebSocket({
    url: `/ws/executions/${executionId}`,
    onMessage: onUpdate,
    reconnect: true,
  });
}
