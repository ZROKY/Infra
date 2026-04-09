// ---------------------------------------------------------------------------
// ZROKY Trust Score — shared TypeScript types
// ---------------------------------------------------------------------------

export type TrustStatus = 'TRUSTED' | 'CAUTION' | 'AT_RISK' | 'CRITICAL' | 'UNAVAILABLE';
export type ColdStartLabel = 'COLLECTING' | 'PROVISIONAL' | 'BUILDING' | 'STABLE';
export type EngineName = 'safety' | 'grounding' | 'consistency' | 'system';
export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low';
export type IncidentStatus = 'open' | 'investigating' | 'resolved';

export interface EngineScores {
  safety: number;
  grounding: number;
  consistency: number;
  system: number;
}

export interface CoverageData {
  score: number;
  band: string;
}

export interface TrustScoreData {
  score: number;
  status: TrustStatus;
  engines: EngineScores;
  coverage: CoverageData;
  last_event_at: string;
  cold_start_label: ColdStartLabel;
}

export interface ApiMeta {
  request_id: string;
  timestamp: string;
  version: string;
}

export interface TrustScoreResponse {
  ok: true;
  data: TrustScoreData;
  meta: ApiMeta;
}

export interface TrustScoreHistoryPoint {
  timestamp: string;
  score: number;
  engines: EngineScores;
}

export interface TrustScoreHistoryResponse {
  ok: true;
  data: { data_points: TrustScoreHistoryPoint[] };
  meta: ApiMeta;
}

export interface Incident {
  incident_id: string;
  engine: EngineName;
  severity: IncidentSeverity;
  status: IncidentStatus;
  title: string;
  evidence: Record<string, unknown>;
  suggested_action: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentsResponse {
  ok: true;
  data: { incidents: Incident[]; cursor: string | null };
  meta: ApiMeta;
}

export interface Agent {
  agent_id: string;
  name: string;
  tier: 'developer' | 'smb' | 'growth' | 'enterprise';
  created_at: string;
}

export interface AgentsResponse {
  ok: true;
  data: { agents: Agent[] };
  meta: ApiMeta;
}

// WebSocket event payloads
export interface WsTrustScoreUpdate {
  agent_id: string;
  score: number;
  status: TrustStatus;
  engines: EngineScores;
  coverage: CoverageData;
  cold_start_label: ColdStartLabel;
  timestamp: string;
}

export interface WsAlertEvent {
  alert_id: string;
  agent_id: string;
  engine: EngineName;
  severity: IncidentSeverity;
  title: string;
  message: string;
  timestamp: string;
}
