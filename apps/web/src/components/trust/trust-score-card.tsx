'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { STATUS_CONFIG, COLD_START_CONFIG } from '@/lib/trust-utils';
import { cn } from '@/lib/utils';
import type { TrustScoreData } from '@/types';

interface TrustScoreCardProps {
  data: TrustScoreData | undefined;
  isLoading?: boolean;
}

export function TrustScoreCard({ data, isLoading }: TrustScoreCardProps) {
  if (isLoading || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Trust Score</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-20 w-32 mx-auto" />
          <Skeleton className="h-4 w-48 mx-auto" />
          <Skeleton className="h-2 w-full" />
        </CardContent>
      </Card>
    );
  }

  const statusCfg = STATUS_CONFIG[data.status];
  const coldStart = COLD_START_CONFIG[data.cold_start_label];
  const isCollecting = data.cold_start_label === 'COLLECTING';

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>Trust Score</CardTitle>
          {data.cold_start_label !== 'STABLE' && (
            <Badge variant="secondary">{coldStart.label}</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {isCollecting ? (
          <div className="text-center py-4">
            <p className="text-2xl font-mono text-zinc-400">—</p>
            <p className="text-sm text-zinc-500 mt-1">{coldStart.description}</p>
          </div>
        ) : (
          <>
            <div className="text-center">
              <span
                className="text-6xl font-mono font-bold"
                style={{ color: statusCfg.color }}
              >
                {Math.round(data.score)}
              </span>
              <div className="mt-2">
                <Badge
                  className={cn('text-sm px-3 py-1')}
                  style={{ backgroundColor: `${statusCfg.color}15`, color: statusCfg.color }}
                >
                  {statusCfg.label}
                </Badge>
              </div>
            </div>

            {/* Coverage */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-sm">
                <span className="text-zinc-500">Coverage</span>
                <span className="font-mono font-medium">{Math.round(data.coverage.score)}%</span>
              </div>
              <Progress
                value={data.coverage.score}
                indicatorClassName={data.coverage.score < 50 ? 'bg-amber-500' : 'bg-green-500'}
              />
              {data.coverage.score < 50 && (
                <p className="text-xs text-amber-600">⚠️ Low coverage — score may not reflect full behavior</p>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
