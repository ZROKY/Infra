// ---------------------------------------------------------------------------
// ZROKY — SWR hooks for data fetching
// ---------------------------------------------------------------------------

import useSWR from 'swr';

import { getTrustScore, getTrustScoreHistory, getIncidents, getAgents } from '@/lib/api';
import type { TrustScoreResponse, TrustScoreHistoryResponse, IncidentsResponse, AgentsResponse } from '@/types';

export function useTrustScore(agentId: string | undefined) {
  return useSWR<TrustScoreResponse>(
    agentId ? [`trust-score`, agentId] : null,
    () => getTrustScore(agentId!),
    { refreshInterval: 10_000 },
  );
}

export function useTrustScoreHistory(agentId: string | undefined, period = '30d') {
  return useSWR<TrustScoreHistoryResponse>(
    agentId ? [`trust-score-history`, agentId, period] : null,
    () => getTrustScoreHistory(agentId!, period),
    { refreshInterval: 60_000 },
  );
}

export function useIncidents(agentId?: string, status?: string) {
  return useSWR<IncidentsResponse>(
    ['incidents', agentId, status],
    () => getIncidents({ agent_id: agentId, status, limit: 50 }),
    { refreshInterval: 30_000 },
  );
}

export function useAgents() {
  return useSWR<AgentsResponse>(
    'agents',
    () => getAgents(),
    { refreshInterval: 60_000 },
  );
}
