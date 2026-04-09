'use client';

import { createContext, useContext, useEffect, useRef, useState, useCallback, type ReactNode } from 'react';
import { io, type Socket } from 'socket.io-client';

import type { WsTrustScoreUpdate, WsAlertEvent } from '@/types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? 'http://localhost:8000';

interface SocketContextValue {
  connected: boolean;
  trustScoreUpdate: WsTrustScoreUpdate | null;
  alerts: WsAlertEvent[];
  clearAlerts: () => void;
}

const SocketContext = createContext<SocketContextValue>({
  connected: false,
  trustScoreUpdate: null,
  alerts: [],
  clearAlerts: () => {},
});

export function useSocket() {
  return useContext(SocketContext);
}

interface SocketProviderProps {
  children: ReactNode;
  token?: string;
}

export function SocketProvider({ children, token }: SocketProviderProps) {
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [trustScoreUpdate, setTrustScoreUpdate] = useState<WsTrustScoreUpdate | null>(null);
  const [alerts, setAlerts] = useState<WsAlertEvent[]>([]);

  const clearAlerts = useCallback(() => setAlerts([]), []);

  useEffect(() => {
    const socket = io(WS_URL, {
      auth: token ? { token } : undefined,
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 10000,
    });

    socketRef.current = socket;

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));

    socket.on('trust_score_update', (data: WsTrustScoreUpdate) => {
      setTrustScoreUpdate(data);
    });

    socket.on('alert', (data: WsAlertEvent) => {
      setAlerts((prev) => [data, ...prev].slice(0, 100));
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [token]);

  return (
    <SocketContext.Provider value={{ connected, trustScoreUpdate, alerts, clearAlerts }}>
      {children}
    </SocketContext.Provider>
  );
}
