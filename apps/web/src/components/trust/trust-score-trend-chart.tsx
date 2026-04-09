'use client';

import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { TrustScoreHistoryPoint } from '@/types';

interface TrustScoreTrendChartProps {
  data: TrustScoreHistoryPoint[] | undefined;
  isLoading?: boolean;
  variant?: 'full' | 'sparkline';
  title?: string;
}

export function TrustScoreTrendChart({
  data,
  isLoading,
  variant = 'full',
  title = '30-Day Trust Score Trend',
}: TrustScoreTrendChartProps) {
  const chartData = useMemo(() => {
    if (!data) return [];
    return data.map((p) => ({
      time: new Date(p.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      score: Math.round(p.score),
      safety: Math.round(p.engines.safety),
      grounding: Math.round(p.engines.grounding),
      consistency: Math.round(p.engines.consistency),
      system: Math.round(p.engines.system),
    }));
  }, [data]);

  if (variant === 'sparkline') {
    if (isLoading || chartData.length === 0) {
      return <Skeleton className="h-10 w-24" />;
    }
    return (
      <div className="h-10 w-24">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0c8ee9" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#0c8ee9" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="score" stroke="#0c8ee9" fill="url(#sparkGrad)" strokeWidth={1.5} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (isLoading || chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
              <XAxis dataKey="time" tick={{ fontSize: 12 }} stroke="#a1a1aa" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="#a1a1aa" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e4e4e7',
                  borderRadius: 8,
                  fontSize: 13,
                }}
              />
              <Line type="monotone" dataKey="score" stroke="#0c8ee9" strokeWidth={2} dot={false} name="Trust Score" />
              <Line type="monotone" dataKey="safety" stroke="#22c55e" strokeWidth={1} dot={false} opacity={0.5} name="Safety" />
              <Line type="monotone" dataKey="grounding" stroke="#f59e0b" strokeWidth={1} dot={false} opacity={0.5} name="Grounding" />
              <Line type="monotone" dataKey="consistency" stroke="#8b5cf6" strokeWidth={1} dot={false} opacity={0.5} name="Consistency" />
              <Line type="monotone" dataKey="system" stroke="#6b7280" strokeWidth={1} dot={false} opacity={0.5} name="System" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
