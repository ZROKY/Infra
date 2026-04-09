// ---------------------------------------------------------------------------
// ZROKY API client — REST calls to the backend
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/v1';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  });

  if (!res.ok) {
    throw new ApiError(res.status, `API ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

// ---- Trust Score ----------------------------------------------------------

import type {
  TrustScoreResponse,
  TrustScoreHistoryResponse,
  IncidentsResponse,
  AgentsResponse,
} from '@/types';

export function getTrustScore(agentId: string): Promise<TrustScoreResponse> {
  return request<TrustScoreResponse>(`/trust-score/${agentId}`);
}

export function getTrustScoreHistory(
  agentId: string,
  period = '30d',
  granularity = '1h',
): Promise<TrustScoreHistoryResponse> {
  return request<TrustScoreHistoryResponse>(
    `/trust-score/${agentId}/history?period=${period}&granularity=${granularity}`,
  );
}

// ---- Incidents ------------------------------------------------------------

export function getIncidents(params: {
  agent_id?: string;
  status?: string;
  severity?: string;
  cursor?: string;
  limit?: number;
}): Promise<IncidentsResponse> {
  const qs = new URLSearchParams();
  if (params.agent_id) qs.set('agent_id', params.agent_id);
  if (params.status) qs.set('status', params.status);
  if (params.severity) qs.set('severity', params.severity);
  if (params.cursor) qs.set('cursor', params.cursor);
  if (params.limit) qs.set('limit', String(params.limit));
  return request<IncidentsResponse>(`/incidents?${qs.toString()}`);
}

// ---- Agents ---------------------------------------------------------------

export function getAgents(): Promise<AgentsResponse> {
  return request<AgentsResponse>('/agents');
}
