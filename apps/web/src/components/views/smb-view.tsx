'use client';

import { TrustScoreCard, EngineScoresSummary, TrustScoreTrendChart, AlertFeed, ColdStartIndicator } from '@/components/trust';
import { useTrustScore, useTrustScoreHistory, useIncidents } from '@/hooks/use-trust-data';

interface SmBViewProps {
  agentId: string;
  onViewAlerts?: () => void;
  onSwitchToEngineer?: () => void;
}

export function SmBView({ agentId, onViewAlerts, onSwitchToEngineer }: SmBViewProps) {
  const { data: scoreResp, isLoading: scoreLoading } = useTrustScore(agentId);
  const { data: historyResp, isLoading: historyLoading } = useTrustScoreHistory(agentId);
  const { data: incidentsResp, isLoading: incidentsLoading } = useIncidents(agentId, 'open');

  const trustData = scoreResp?.data;
  const historyData = historyResp?.data.data_points;
  const incidents = incidentsResp?.data.incidents;

  return (
    <div className="space-y-6">
      {/* Cold-start banner */}
      {trustData && trustData.cold_start_label !== 'STABLE' && (
        <ColdStartIndicator label={trustData.cold_start_label} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          <TrustScoreCard data={trustData} isLoading={scoreLoading} />
          <TrustScoreTrendChart data={historyData} isLoading={historyLoading} variant="sparkline" />
        </div>

        {/* Right column */}
        <div className="space-y-6">
          <AlertFeed
            incidents={incidents}
            isLoading={incidentsLoading}
            onViewAll={onViewAlerts}
          />
          <EngineScoresSummary
            engines={trustData?.engines}
            isLoading={scoreLoading}
            onEngineClick={onSwitchToEngineer ? () => onSwitchToEngineer() : undefined}
          />
        </div>
      </div>
    </div>
  );
}
