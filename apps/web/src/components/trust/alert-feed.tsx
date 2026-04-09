'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { formatRelativeTime } from '@/lib/trust-utils';
import { cn } from '@/lib/utils';
import type { Incident, WsAlertEvent } from '@/types';

type AlertItem = Incident | WsAlertEvent;

interface AlertFeedProps {
  incidents: Incident[] | undefined;
  wsAlerts?: WsAlertEvent[];
  isLoading?: boolean;
  maxItems?: number;
  onViewAll?: () => void;
}

function isIncident(item: AlertItem): item is Incident {
  return 'incident_id' in item;
}

const SEVERITY_VARIANT: Record<string, 'danger' | 'warning' | 'secondary'> = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'secondary',
};

export function AlertFeed({ incidents, wsAlerts = [], isLoading, maxItems = 10, onViewAll }: AlertFeedProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const allItems: AlertItem[] = [
    ...wsAlerts,
    ...(incidents ?? []),
  ].slice(0, maxItems);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>Recent Alerts</CardTitle>
          {allItems.length > 0 && onViewAll && (
            <button onClick={onViewAll} className="text-xs text-zroky-600 hover:underline">
              View All Alerts →
            </button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {allItems.length === 0 ? (
          <p className="text-sm text-zinc-400 text-center py-6">No recent alerts</p>
        ) : (
          <ScrollArea className="h-72">
            <div className="space-y-2 pr-3">
              {allItems.map((item) => {
                const id = isIncident(item) ? item.incident_id : item.alert_id;
                const severity = item.severity;
                const title = item.title;
                const engine = item.engine;
                const time = isIncident(item) ? item.created_at : item.timestamp;

                return (
                  <div
                    key={id}
                    className={cn(
                      'flex items-start gap-3 rounded-lg border p-3 text-sm',
                      severity === 'critical' && 'border-red-200 bg-red-50/50',
                      severity === 'high' && 'border-red-100 bg-red-50/30',
                      severity === 'medium' && 'border-amber-200 bg-amber-50/30',
                      severity === 'low' && 'border-zinc-200',
                    )}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <Badge variant={SEVERITY_VARIANT[severity] ?? 'secondary'} className="text-[10px]">
                          {severity.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-zinc-400 capitalize">{engine}</span>
                      </div>
                      <p className="font-medium truncate">{title}</p>
                    </div>
                    <span className="text-xs text-zinc-400 whitespace-nowrap">{formatRelativeTime(time)}</span>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
