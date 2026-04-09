'use client';

import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { COLD_START_CONFIG } from '@/lib/trust-utils';
import type { ColdStartLabel } from '@/types';

interface ColdStartIndicatorProps {
  label: ColdStartLabel;
}

const PROGRESS_MAP: Record<ColdStartLabel, number> = {
  COLLECTING: 10,
  PROVISIONAL: 35,
  BUILDING: 65,
  STABLE: 100,
};

export function ColdStartIndicator({ label }: ColdStartIndicatorProps) {
  if (label === 'STABLE') return null;

  const cfg = COLD_START_CONFIG[label];
  const progress = PROGRESS_MAP[label];

  return (
    <div className="flex items-center gap-3">
      <Badge variant="secondary" className="text-xs whitespace-nowrap">
        {cfg.label}
      </Badge>
      <div className="flex-1">
        <Progress value={progress} indicatorClassName="bg-zroky-500" className="h-1.5" />
      </div>
      <span className="text-xs text-zinc-400">{cfg.description}</span>
    </div>
  );
}
