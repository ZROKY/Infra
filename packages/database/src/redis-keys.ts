/**
 * ZROKY Redis Key Patterns
 *
 * All Redis keys are namespaced by client_id to enforce multi-tenant isolation.
 * TTL values match V1 Scope specification.
 */

// ── TTL Constants (seconds) ──────────────────
export const REDIS_TTL = {
  TRUST_SCORE: 60,           // 60s — real-time scores
  ENGINE_SCORES: 60,         // 60s — per-engine breakdown
  ALERT_COUNT: 86_400,       // 24h — daily alert counter
  API_RATE_LIMIT: 60,        // 1min — rate limit window
  CLIENT_CONFIG: 300,        // 5min — cached client config
  BADGE_SCORE: 30,           // 30s — public badge score
  SCAN_RATE: 86_400,         // 24h — health check rate limit
} as const;

// ── Key Builders ─────────────────────────────
export const RedisKeys = {
  /** Current trust score for an agent: JSON { total, safety, grounding, consistency, system, coverage } */
  trustScore: (clientId: string, agentId: string) =>
    `trust_score:${clientId}:${agentId}` as const,

  /** Per-engine score breakdown: JSON { safety, grounding, consistency, system, coverage, details } */
  engineScores: (clientId: string, agentId: string) =>
    `engine_scores:${clientId}:${agentId}` as const,

  /** 24h alert count for client: Integer */
  alertCount: (clientId: string) =>
    `alert_count:${clientId}:24h` as const,

  /** API rate limit counter per key: Integer */
  apiRateLimit: (apiKeyHash: string) =>
    `api_rate_limit:${apiKeyHash}` as const,

  /** Cached client configuration: JSON */
  clientConfig: (clientId: string) =>
    `client_config:${clientId}` as const,

  /** Public badge score (embeddable): JSON { score, band, updated_at } */
  badgeScore: (agentId: string) =>
    `badge_score:${agentId}` as const,

  /** Health check scan rate limit per IP hash: Integer */
  scanRate: (ipHash: string) =>
    `scan_rate:${ipHash}` as const,
} as const;

// ── Types for stored values ──────────────────
export interface RedisTrustScore {
  total: number;
  safety: number;
  grounding: number;
  consistency: number;
  system: number;
  coverage: number;
  updated_at: string;
}

export interface RedisEngineScores {
  safety: number;
  grounding: number;
  consistency: number;
  system: number;
  coverage: number;
  details: Record<string, unknown>;
}

export interface RedisBadgeScore {
  score: number;
  band: 'critical' | 'low' | 'medium' | 'high' | 'excellent';
  updated_at: string;
}

export interface RedisClientConfig {
  tier: string;
  max_agents: number;
  max_interactions_month: number;
  features: Record<string, boolean>;
}
