'use client';

import { useMemo } from 'react';

import {
  PortfolioHeader,
  AgentPortfolioTable,
  MultiAgentTrendChart,
  KeyMetricsBar,
} from '@/components/trust';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useAgents, useIncidents } from '@/hooks/use-trust-data';

interface ExecutiveViewProps {
  onAgentClick?: (agentId: string) => void;
}

export function ExecutiveView({ onAgentClick }: ExecutiveViewProps) {
  const { data: agentsResp, isLoading: agentsLoading } = useAgents();
  const { data: incidentsResp } = useIncidents();

  const agents = useMemo(() => agentsResp?.data.agents ?? [], [agentsResp]);
  const incidents = useMemo(() => incidentsResp?.data.incidents ?? [], [incidentsResp]);

  // Build portfolio summary data
  const portfolioAgents = useMemo(() => {
    return agents.map((a) => ({
      agent_id: a.agent_id,
      name: a.name,
      score: 0, // Will be populated by individual score fetches
      openIncidents: incidents.filter(
        (i) => i.status !== 'resolved',
      ).length,
    }));
  }, [agents, incidents]);

  const keyMetrics = useMemo(() => {
    const resolved = incidents.filter((i) => i.status === 'resolved').length;
    const engineCounts: Record<string, number> = {};
    for (const inc of incidents.filter((i) => i.status !== 'resolved')) {
      engineCounts[inc.engine] = (engineCounts[inc.engine] ?? 0) + 1;
    }
    const worstEngine = Object.entries(engineCounts).sort(([, a], [, b]) => b - a)[0]?.[0] ?? 'None';

    return {
      totalEvents: 0, // Would come from analytics endpoint
      totalIncidents: incidents.length,
      resolvedCount: resolved,
      worstEngine: worstEngine.charAt(0).toUpperCase() + worstEngine.slice(1),
    };
  }, [incidents]);

  if (agentsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-zinc-400">No agents found for this organization.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <PortfolioHeader agents={portfolioAgents.map((a) => ({ name: a.name, score: a.score }))} />

      <KeyMetricsBar
        totalEvents={keyMetrics.totalEvents}
        totalIncidents={keyMetrics.totalIncidents}
        resolvedCount={keyMetrics.resolvedCount}
        worstEngine={keyMetrics.worstEngine}
      />

      <AgentPortfolioTable
        agents={portfolioAgents}
        isLoading={agentsLoading}
        onAgentClick={onAgentClick}
      />

      <MultiAgentTrendChart agents={[]} isLoading={false} />
    </div>
  );
}
