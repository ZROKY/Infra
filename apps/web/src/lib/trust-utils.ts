// ---------------------------------------------------------------------------
// ZROKY — Trust score display helpers
// ---------------------------------------------------------------------------

import type { TrustStatus, ColdStartLabel, EngineName } from '@/types';

export const STATUS_CONFIG: Record<TrustStatus, { label: string; color: string; bg: string }> = {
  TRUSTED: { label: 'Trusted', color: '#22C55E', bg: 'bg-green-500/10' },
  CAUTION: { label: 'Caution', color: '#F59E0B', bg: 'bg-amber-500/10' },
  AT_RISK: { label: 'At Risk', color: '#F97316', bg: 'bg-orange-500/10' },
  CRITICAL: { label: 'Critical', color: '#EF4444', bg: 'bg-red-500/10' },
  UNAVAILABLE: { label: 'Unavailable', color: '#6B7280', bg: 'bg-gray-500/10' },
};

export const COLD_START_CONFIG: Record<ColdStartLabel, { label: string; description: string }> = {
  COLLECTING: { label: 'Collecting', description: 'Collecting data…' },
  PROVISIONAL: { label: 'Provisional', description: 'Score based on limited data' },
  BUILDING: { label: 'Building', description: 'Score becoming more reliable' },
  STABLE: { label: 'Stable', description: 'Score based on sufficient data' },
};

export const ENGINE_CONFIG: Record<EngineName, { label: string; weight: string; icon: string }> = {
  safety: { label: 'Safety', weight: '30%', icon: '🛡️' },
  grounding: { label: 'Grounding', weight: '25%', icon: '🎯' },
  consistency: { label: 'Consistency', weight: '20%', icon: '📊' },
  system: { label: 'System', weight: '10%', icon: '⚙️' },
};

export function getStatusForScore(score: number): TrustStatus {
  if (score >= 90) return 'TRUSTED';
  if (score >= 75) return 'CAUTION';
  if (score >= 60) return 'AT_RISK';
  return 'CRITICAL';
}

export function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function trendArrow(current: number, previous: number): '↗' | '→' | '↘' {
  const delta = current - previous;
  if (delta > 2) return '↗';
  if (delta < -2) return '↘';
  return '→';
}
