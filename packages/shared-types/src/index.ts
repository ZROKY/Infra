/**
 * Shared type definitions for ZROKY platform.
 * Types are added as features are built.
 */

export type TrustScoreStatus = 'BUILDING' | 'PROVISIONAL' | 'STABLE';

export type TrustScoreBand = 'CRITICAL' | 'WARNING' | 'FAIR' | 'GOOD' | 'EXCELLENT';

export interface TrustScore {
  score: number;
  status: TrustScoreStatus;
  band: TrustScoreBand;
  engines: {
    safety: number;
    grounding: number;
    consistency: number;
    system: number;
  };
  coverage: number;
  overrideApplied: boolean;
  computedAt: string;
}

export interface ApiEnvelope<T = unknown> {
  success: boolean;
  data: T | null;
  error: {
    code: string;
    message: string;
    docUrl?: string;
    retryAfter?: number;
  } | null;
  meta: {
    requestId: string;
    timestamp: string;
    version?: string;
  };
  pagination?: {
    hasMore: boolean;
    nextCursor?: string;
  };
}
