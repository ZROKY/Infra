'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ENGINE_CONFIG, STATUS_CONFIG, getStatusForScore } from '@/lib/trust-utils';
import { cn } from '@/lib/utils';
import type { EngineScores, EngineName } from '@/types';

interface EngineScoresSummaryProps {
  engines: EngineScores | undefined;
  isLoading?: boolean;
  onEngineClick?: (engine: EngineName) => void;
}

export function EngineScoresSummary({ engines, isLoading, onEngineClick }: EngineScoresSummaryProps) {
  if (isLoading || !engines) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Engine Scores</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const engineEntries = (Object.entries(engines) as [EngineName, number][]).sort(
    ([, a], [, b]) => b - a,
  );

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle>Engine Scores</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {engineEntries.map(([name, score]) => {
          const cfg = ENGINE_CONFIG[name];
          const status = getStatusForScore(score);
          const statusCfg = STATUS_CONFIG[status];

          return (
            <button
              key={name}
              onClick={() => onEngineClick?.(name)}
              className={cn(
                'flex items-center justify-between w-full rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-zinc-50',
                onEngineClick && 'cursor-pointer',
              )}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-lg">{cfg.icon}</span>
                <div>
                  <p className="text-sm font-medium">{cfg.label}</p>
                  <p className="text-xs text-zinc-400">{cfg.weight} weight</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-lg font-semibold" style={{ color: statusCfg.color }}>
                  {Math.round(score)}
                </span>
                {status === 'TRUSTED' && <span className="text-green-500">✓</span>}
                {(status === 'AT_RISK' || status === 'CRITICAL') && <span className="text-red-500">⚠</span>}
              </div>
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
}
