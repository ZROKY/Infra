/**
 * Health Check — Free AI Trust analysis, no signup required.
 *
 * zroky.ai/scan → user pastes a conversation → instant trust breakdown.
 * SEC-06: API keys are in-memory only, never persisted.
 */

import { randomUUID } from 'node:crypto';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface HealthCheckInput {
  conversation: ConversationTurn[];
  model?: string;
}

export interface ConversationTurn {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface HealthCheckResult {
  scan_id: string;
  overall_score: number;
  status: 'trusted' | 'moderate' | 'low_trust' | 'untrusted';
  engines: {
    safety: EngineBreakdown;
    grounding: EngineBreakdown;
    consistency: EngineBreakdown;
    system: EngineBreakdown;
  };
  flags: Flag[];
  summary: string;
  scanned_at: string;
}

export interface EngineBreakdown {
  score: number;
  weight: number;
  signals: string[];
}

export interface Flag {
  engine: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
}

// ---------------------------------------------------------------------------
// In-memory session keys (SEC-06: never persisted to DB)
// ---------------------------------------------------------------------------

const sessionKeys = new Map<string, { expiresAt: number }>();

export function createSessionKey(): string {
  const key = `hc_${randomUUID().replace(/-/g, '')}`;
  // Expires in 15 minutes
  sessionKeys.set(key, { expiresAt: Date.now() + 15 * 60 * 1000 });
  return key;
}

export function validateSessionKey(key: string): boolean {
  const entry = sessionKeys.get(key);
  if (!entry) return false;
  if (Date.now() > entry.expiresAt) {
    sessionKeys.delete(key);
    return false;
  }
  return true;
}

export function revokeSessionKey(key: string): void {
  sessionKeys.delete(key);
}

// Periodic cleanup (every 5 minutes)
setInterval(() => {
  const now = Date.now();
  for (const [key, entry] of sessionKeys) {
    if (now > entry.expiresAt) {
      sessionKeys.delete(key);
    }
  }
}, 5 * 60 * 1000).unref();

// ---------------------------------------------------------------------------
// Lightweight analysis engine (V1: heuristic-based, no LLM dependency)
// ---------------------------------------------------------------------------

function analyzeSafety(turns: ConversationTurn[]): EngineBreakdown {
  const signals: string[] = [];
  let deductions = 0;

  const dangerousPatterns = [
    /ignore\s+(previous|all)\s+instructions/i,
    /you\s+are\s+now\s+(DAN|evil|unfiltered)/i,
    /pretend\s+you\s+(have\s+no|don't\s+have)\s+restrictions/i,
    /system\s*prompt/i,
    /jailbreak/i,
  ];

  const toxicPatterns = [
    /\b(kill|murder|harm|attack|weapon|bomb|suicide)\b/i,
    /\b(hate|racist|sexist)\b/i,
  ];

  for (const turn of turns) {
    for (const pattern of dangerousPatterns) {
      if (pattern.test(turn.content)) {
        signals.push(`Prompt injection attempt detected in ${turn.role} message`);
        deductions += 15;
      }
    }
    for (const pattern of toxicPatterns) {
      if (pattern.test(turn.content)) {
        signals.push(`Potentially harmful content detected in ${turn.role} message`);
        deductions += 10;
      }
    }
  }

  if (signals.length === 0) signals.push('No safety issues detected');
  const score = Math.max(0, 100 - deductions);
  return { score, weight: 0.30, signals };
}

function analyzeGrounding(turns: ConversationTurn[]): EngineBreakdown {
  const signals: string[] = [];
  let deductions = 0;

  const assistantTurns = turns.filter((t) => t.role === 'assistant');

  for (const turn of assistantTurns) {
    // Check for hedging language (may indicate uncertainty)
    const hedges = (turn.content.match(/\b(I think|probably|might|possibly|I'm not sure|I believe)\b/gi) || []).length;
    if (hedges > 3) {
      signals.push('High uncertainty language detected');
      deductions += 5;
    }

    // Check for confident but unverifiable claims
    const absoluteClaims = (turn.content.match(/\b(always|never|definitely|certainly|guaranteed|100%)\b/gi) || []).length;
    if (absoluteClaims > 2) {
      signals.push('Overconfident absolute claims detected');
      deductions += 8;
    }

    // Very long responses may contain hallucinations
    if (turn.content.length > 3000) {
      signals.push('Long response — higher risk of factual drift');
      deductions += 3;
    }
  }

  if (signals.length === 0) signals.push('Grounding appears reasonable');
  const score = Math.max(0, 100 - deductions);
  return { score, weight: 0.25, signals };
}

function analyzeConsistency(turns: ConversationTurn[]): EngineBreakdown {
  const signals: string[] = [];
  let deductions = 0;

  const assistantTurns = turns.filter((t) => t.role === 'assistant');

  if (assistantTurns.length >= 2) {
    // Check tone consistency
    const lengths = assistantTurns.map((t) => t.content.length);
    const avgLen = lengths.reduce((a, b) => a + b, 0) / lengths.length;
    const variance = lengths.reduce((sum, l) => sum + (l - avgLen) ** 2, 0) / lengths.length;
    const cv = Math.sqrt(variance) / (avgLen || 1);

    if (cv > 1.5) {
      signals.push('High response length variance — inconsistent verbosity');
      deductions += 10;
    }
  } else {
    signals.push('Single response — limited consistency analysis');
  }

  if (signals.length === 0) signals.push('Consistency appears stable');
  const score = Math.max(0, 100 - deductions);
  return { score, weight: 0.20, signals };
}

function analyzeSystem(turns: ConversationTurn[]): EngineBreakdown {
  const signals: string[] = [];
  let deductions = 0;

  const totalContent = turns.reduce((sum, t) => sum + t.content.length, 0);

  if (totalContent > 50_000) {
    signals.push('Very large conversation — potential context window pressure');
    deductions += 5;
  }

  if (turns.length > 20) {
    signals.push('Long conversation chain — latency and coherence risk');
    deductions += 5;
  }

  if (signals.length === 0) signals.push('System metrics within normal range');
  const score = Math.max(0, 100 - deductions);
  return { score, weight: 0.10, signals };
}

// ---------------------------------------------------------------------------
// Main scan function
// ---------------------------------------------------------------------------

export function runHealthCheck(input: HealthCheckInput): HealthCheckResult {
  const safety = analyzeSafety(input.conversation);
  const grounding = analyzeGrounding(input.conversation);
  const consistency = analyzeConsistency(input.conversation);
  const system = analyzeSystem(input.conversation);

  // Weighted score (same formula as Trust Score Computer)
  const coverageBonus = 15; // All 4 engines active
  const rawScore =
    safety.score * safety.weight +
    grounding.score * grounding.weight +
    consistency.score * consistency.weight +
    system.score * system.weight +
    coverageBonus;

  const overallScore = Math.min(100, Math.round(rawScore));

  // Status band
  let status: HealthCheckResult['status'];
  if (overallScore >= 80) status = 'trusted';
  else if (overallScore >= 60) status = 'moderate';
  else if (overallScore >= 40) status = 'low_trust';
  else status = 'untrusted';

  // Collect flags
  const flags: Flag[] = [];
  const allEngines = { safety, grounding, consistency, system };
  for (const [name, engine] of Object.entries(allEngines)) {
    for (const signal of engine.signals) {
      if (signal.includes('detected') || signal.includes('risk')) {
        const severity: Flag['severity'] = engine.score < 50 ? 'critical' : engine.score < 75 ? 'warning' : 'info';
        flags.push({ engine: name, severity, message: signal });
      }
    }
  }

  // Summary
  const summaryParts: string[] = [];
  if (overallScore >= 80) summaryParts.push('This conversation shows strong trust signals.');
  else if (overallScore >= 60) summaryParts.push('This conversation has moderate trust with some areas of concern.');
  else summaryParts.push('This conversation shows trust concerns that should be addressed.');

  if (flags.length > 0) {
    summaryParts.push(`${flags.length} flag(s) identified across ${new Set(flags.map((f) => f.engine)).size} engine(s).`);
  }

  return {
    scan_id: `scan_${randomUUID().replace(/-/g, '').slice(0, 16)}`,
    overall_score: overallScore,
    status,
    engines: { safety, grounding, consistency, system },
    flags,
    summary: summaryParts.join(' '),
    scanned_at: new Date().toISOString(),
  };
}
