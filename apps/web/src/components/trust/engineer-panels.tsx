'use client';

import { ChevronDown, ChevronUp, RotateCcw, TestTube2, X } from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ENGINE_CONFIG, STATUS_CONFIG, getStatusForScore, formatRelativeTime } from '@/lib/trust-utils';
import type { Incident, EngineName, EngineScores } from '@/types';

// -- Engine Table -----------------------------------------------------------

interface EngineTableProps {
  engines: EngineScores | undefined;
  incidents: Incident[] | undefined;
  isLoading?: boolean;
}

export function EngineTable({ engines, incidents, isLoading }: EngineTableProps) {
  if (isLoading || !engines) {
    return (
      <Card>
        <CardHeader><CardTitle>Engine Breakdown</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-40 w-full" /></CardContent>
      </Card>
    );
  }

  const engineNames: EngineName[] = ['safety', 'grounding', 'consistency', 'system'];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle>Engine Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-zinc-500">
                <th className="pb-2 font-medium">Engine</th>
                <th className="pb-2 font-medium text-right">Score</th>
                <th className="pb-2 font-medium text-right">Open Incidents</th>
                <th className="pb-2 font-medium text-right">Status</th>
              </tr>
            </thead>
            <tbody>
              {engineNames.map((name) => {
                const score = engines[name];
                const status = getStatusForScore(score);
                const statusCfg = STATUS_CONFIG[status];
                const cfg = ENGINE_CONFIG[name];
                const openCount = incidents?.filter((i) => i.engine === name && i.status !== 'resolved').length ?? 0;

                return (
                  <tr key={name} className="border-b last:border-0">
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <span>{cfg.icon}</span>
                        <span className="font-medium">{cfg.label}</span>
                        <span className="text-zinc-400 text-xs">({cfg.weight})</span>
                      </div>
                    </td>
                    <td className="py-3 text-right">
                      <span className="font-mono font-semibold" style={{ color: statusCfg.color }}>
                        {Math.round(score)}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      {openCount > 0 ? (
                        <Badge variant="danger">{openCount}</Badge>
                      ) : (
                        <span className="text-zinc-400">0</span>
                      )}
                    </td>
                    <td className="py-3 text-right">
                      <Badge
                        style={{ backgroundColor: `${statusCfg.color}15`, color: statusCfg.color }}
                      >
                        {statusCfg.label}
                      </Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

// -- Incident Detail Panel --------------------------------------------------

interface IncidentDetailPanelProps {
  incidents: Incident[] | undefined;
  isLoading?: boolean;
}

const SEVERITY_VARIANT: Record<string, 'danger' | 'warning' | 'secondary'> = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'secondary',
};

export function IncidentDetailPanel({ incidents, isLoading }: IncidentDetailPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Incidents</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const openIncidents = incidents?.filter((i) => i.status !== 'resolved') ?? [];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>Incidents</CardTitle>
          {openIncidents.length > 0 && (
            <Badge variant="danger">{openIncidents.length} open</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {openIncidents.length === 0 ? (
          <p className="text-sm text-zinc-400 text-center py-6">No open incidents</p>
        ) : (
          <div className="space-y-2">
            {openIncidents.map((incident) => {
              const isExpanded = expandedId === incident.incident_id;
              const cfg = ENGINE_CONFIG[incident.engine];

              return (
                <div key={incident.incident_id} className="border rounded-lg">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : incident.incident_id)}
                    className="flex items-center justify-between w-full p-3 text-left hover:bg-zinc-50 rounded-lg transition-colors"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Badge variant={SEVERITY_VARIANT[incident.severity] ?? 'secondary'} className="text-[10px]">
                        {incident.severity.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-zinc-400">{cfg.icon} {cfg.label}</span>
                      <span className="text-sm font-medium truncate">{incident.title}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-zinc-400">{formatRelativeTime(incident.created_at)}</span>
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="px-3 pb-3 space-y-3 border-t">
                      {/* Evidence */}
                      <div className="mt-3">
                        <p className="text-xs font-medium text-zinc-500 mb-1">Evidence</p>
                        <pre className="text-xs bg-zinc-50 rounded-md p-2 overflow-x-auto font-mono">
                          {JSON.stringify(incident.evidence, null, 2)}
                        </pre>
                      </div>

                      {/* Suggested Action */}
                      <div>
                        <p className="text-xs font-medium text-zinc-500 mb-1">Suggested Action</p>
                        <p className="text-sm">{incident.suggested_action}</p>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline">
                          <RotateCcw className="h-3.5 w-3.5 mr-1" /> Re-embed Now
                        </Button>
                        <Button size="sm" variant="outline">
                          <TestTube2 className="h-3.5 w-3.5 mr-1" /> Run Test Suite
                        </Button>
                        <Button size="sm" variant="ghost">
                          <X className="h-3.5 w-3.5 mr-1" /> Dismiss
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
