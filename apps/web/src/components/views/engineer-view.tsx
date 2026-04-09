'use client';

import {
  EngineTable,
  IncidentDetailPanel,
  TrustScoreTrendChart,
  ColdStartIndicator,
} from '@/components/trust';
import { Badge } from '@/components/ui/badge';
import { useTrustScore, useTrustScoreHistory, useIncidents } from '@/hooks/use-trust-data';
import { STATUS_CONFIG } from '@/lib/trust-utils';

interface EngineerViewProps {
  agentId: string;
  agentName?: string;
}

export function EngineerView({ agentId, agentName }: EngineerViewProps) {
  const { data: scoreResp, isLoading: scoreLoading } = useTrustScore(agentId);
  const { data: historyResp, isLoading: historyLoading } = useTrustScoreHistory(agentId);
  const { data: incidentsResp, isLoading: incidentsLoading } = useIncidents(agentId);

  const trustData = scoreResp?.data;
  const historyData = historyResp?.data.data_points;
  const incidents = incidentsResp?.data.incidents;

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex items-center justify-between bg-white rounded-xl border p-4">
        <div className="flex items-center gap-4">
          {agentName && <h2 className="text-lg font-semibold">{agentName}</h2>}
          {trustData && (
            <>
              <span className="text-3xl font-mono font-bold" style={{ color: STATUS_CONFIG[trustData.status].color }}>
                {Math.round(trustData.score)}
              </span>
              <Badge style={{
                backgroundColor: `${STATUS_CONFIG[trustData.status].color}15`,
                color: STATUS_CONFIG[trustData.status].color,
              }}>
                {STATUS_CONFIG[trustData.status].label}
              </Badge>
              <span className="text-sm text-zinc-500">Coverage: {Math.round(trustData.coverage.score)}%</span>
            </>
          )}
        </div>
      </div>

      {/* Cold-start banner */}
      {trustData && trustData.cold_start_label !== 'STABLE' && (
        <ColdStartIndicator label={trustData.cold_start_label} />
      )}

      {/* Engine Table */}
      <EngineTable engines={trustData?.engines} incidents={incidents} isLoading={scoreLoading || incidentsLoading} />

      {/* Incident Detail Panel */}
      <IncidentDetailPanel incidents={incidents} isLoading={incidentsLoading} />

      {/* 30-day Trust Score History */}
      <TrustScoreTrendChart data={historyData} isLoading={historyLoading} />
    </div>
  );
}
