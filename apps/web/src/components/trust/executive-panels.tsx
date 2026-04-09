'use client';

import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { STATUS_CONFIG, getStatusForScore, trendArrow } from '@/lib/trust-utils';
import type { TrustScoreHistoryPoint } from '@/types';

// -- Portfolio Header -------------------------------------------------------

interface PortfolioHeaderProps {
  agents: { name: string; score: number }[];
}

export function PortfolioHeader({ agents }: PortfolioHeaderProps) {
  const avgScore = agents.length > 0
    ? agents.reduce((sum, a) => sum + a.score, 0) / agents.length
    : 0;
  const status = getStatusForScore(avgScore);
  const statusCfg = STATUS_CONFIG[status];

  return (
    <div className="flex items-center justify-between bg-white rounded-xl border p-6">
      <div>
        <p className="text-sm text-zinc-500">Portfolio Trust Score</p>
        <div className="flex items-baseline gap-3 mt-1">
          <span className="text-4xl font-mono font-bold" style={{ color: statusCfg.color }}>
            {Math.round(avgScore)}
          </span>
          <Badge style={{ backgroundColor: `${statusCfg.color}15`, color: statusCfg.color }}>
            {statusCfg.label}
          </Badge>
        </div>
      </div>
      <div className="text-right">
        <p className="text-sm text-zinc-500">Active Agents</p>
        <p className="text-3xl font-mono font-bold mt-1">{agents.length}</p>
      </div>
    </div>
  );
}

// -- Agent Portfolio Table --------------------------------------------------

interface AgentRow {
  agent_id: string;
  name: string;
  score: number;
  previousScore?: number;
  openIncidents: number;
}

interface AgentPortfolioTableProps {
  agents: AgentRow[];
  isLoading?: boolean;
  onAgentClick?: (agentId: string) => void;
}

export function AgentPortfolioTable({ agents, isLoading, onAgentClick }: AgentPortfolioTableProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Agent Portfolio</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-48 w-full" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle>Agent Portfolio</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-zinc-500">
                <th className="pb-2 font-medium">Agent</th>
                <th className="pb-2 font-medium text-right">Score</th>
                <th className="pb-2 font-medium text-center">Status</th>
                <th className="pb-2 font-medium text-center">Trend</th>
                <th className="pb-2 font-medium text-right">Open Incidents</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => {
                const status = getStatusForScore(agent.score);
                const statusCfg = STATUS_CONFIG[status];
                const arrow = agent.previousScore !== undefined
                  ? trendArrow(agent.score, agent.previousScore)
                  : '→';

                return (
                  <tr
                    key={agent.agent_id}
                    className="border-b last:border-0 hover:bg-zinc-50 cursor-pointer transition-colors"
                    onClick={() => onAgentClick?.(agent.agent_id)}
                  >
                    <td className="py-3 font-medium">{agent.name}</td>
                    <td className="py-3 text-right">
                      <span className="font-mono font-semibold" style={{ color: statusCfg.color }}>
                        {Math.round(agent.score)}
                      </span>
                    </td>
                    <td className="py-3 text-center">
                      <Badge style={{ backgroundColor: `${statusCfg.color}15`, color: statusCfg.color }}>
                        {statusCfg.label}
                      </Badge>
                    </td>
                    <td className="py-3 text-center text-lg">{arrow}</td>
                    <td className="py-3 text-right">
                      {agent.openIncidents > 0 ? (
                        <Badge variant="danger">{agent.openIncidents}</Badge>
                      ) : (
                        <span className="text-zinc-400">0</span>
                      )}
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

// -- Multi-Agent Trend Chart ------------------------------------------------

const AGENT_COLORS = ['#0c8ee9', '#22c55e', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899'];

interface MultiAgentTrendChartProps {
  agents: { name: string; history: TrustScoreHistoryPoint[] }[];
  isLoading?: boolean;
}

export function MultiAgentTrendChart({ agents, isLoading }: MultiAgentTrendChartProps) {
  const chartData = useMemo(() => {
    if (agents.length === 0) return [];

    const timeMap = new Map<string, Record<string, number>>();
    for (const agent of agents) {
      for (const point of agent.history) {
        const key = new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const entry = timeMap.get(key) ?? {};
        entry[agent.name] = Math.round(point.score);
        timeMap.set(key, entry);
      }
    }
    return Array.from(timeMap.entries()).map(([time, scores]) => ({ time, ...scores }));
  }, [agents]);

  if (isLoading || chartData.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>30-Day Multi-Agent Trend</CardTitle></CardHeader>
        <CardContent><Skeleton className="h-64 w-full" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>30-Day Multi-Agent Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
              <XAxis dataKey="time" tick={{ fontSize: 12 }} stroke="#a1a1aa" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#a1a1aa" />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e4e4e7', borderRadius: 8, fontSize: 13 }}
              />
              <Legend />
              {agents.map((agent, i) => (
                <Line
                  key={agent.name}
                  type="monotone"
                  dataKey={agent.name}
                  stroke={AGENT_COLORS[i % AGENT_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

// -- Key Metrics Bar --------------------------------------------------------

interface KeyMetricsBarProps {
  totalEvents: number;
  totalIncidents: number;
  resolvedCount: number;
  worstEngine: string;
}

export function KeyMetricsBar({ totalEvents, totalIncidents, resolvedCount, worstEngine }: KeyMetricsBarProps) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {[
        { label: 'Total Events (30d)', value: totalEvents.toLocaleString() },
        { label: 'Total Incidents', value: totalIncidents.toLocaleString() },
        { label: 'Resolved', value: resolvedCount.toLocaleString() },
        { label: 'Worst Engine', value: worstEngine },
      ].map((m) => (
        <Card key={m.label}>
          <CardContent className="pt-6">
            <p className="text-sm text-zinc-500">{m.label}</p>
            <p className="text-2xl font-mono font-bold mt-1">{m.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
