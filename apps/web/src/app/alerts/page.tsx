'use client';

import { Bell, Filter, X } from 'lucide-react';
import { useState } from 'react';

import { Sidebar } from '@/components/layout/sidebar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useIncidents } from '@/hooks/use-trust-data';
import { ENGINE_CONFIG, formatRelativeTime } from '@/lib/trust-utils';
import { useSocket } from '@/providers/socket-provider';
import type { Incident, IncidentSeverity } from '@/types';

const SEVERITY_VARIANT: Record<string, 'danger' | 'warning' | 'secondary'> = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'secondary',
};

export default function AlertCenterPage() {
  const { data: incidentsResp, isLoading } = useIncidents();
  const { alerts: wsAlerts } = useSocket();
  const [severityFilter, setSeverityFilter] = useState<IncidentSeverity | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const incidents = incidentsResp?.data.incidents ?? [];

  const filtered = incidents.filter((inc) => {
    if (severityFilter !== 'all' && inc.severity !== severityFilter) return false;
    if (statusFilter !== 'all' && inc.status !== statusFilter) return false;
    return true;
  });

  const openCount = incidents.filter((i) => i.status !== 'resolved').length;
  const criticalCount = incidents.filter((i) => i.severity === 'critical' && i.status !== 'resolved').length;

  return (
    <div className="flex h-screen">
      <Sidebar currentPath="/alerts" />

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Bell className="h-6 w-6 text-zinc-700" />
              <div>
                <h1 className="text-2xl font-bold">Alert Center</h1>
                <p className="text-sm text-zinc-500">
                  {openCount} open incident{openCount !== 1 ? 's' : ''}
                  {criticalCount > 0 && (
                    <span className="text-red-500 ml-2">({criticalCount} critical)</span>
                  )}
                </p>
              </div>
            </div>

            {/* Real-time alerts badge */}
            {wsAlerts.length > 0 && (
              <Badge variant="danger">{wsAlerts.length} new</Badge>
            )}
          </div>

          {/* Filters */}
          <div className="flex items-center gap-4 mb-6">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-zinc-400" />
              <span className="text-sm text-zinc-500">Severity:</span>
              <Tabs value={severityFilter} onValueChange={(v) => setSeverityFilter(v as IncidentSeverity | 'all')}>
                <TabsList>
                  <TabsTrigger value="all">All</TabsTrigger>
                  <TabsTrigger value="critical">Critical</TabsTrigger>
                  <TabsTrigger value="high">High</TabsTrigger>
                  <TabsTrigger value="medium">Medium</TabsTrigger>
                  <TabsTrigger value="low">Low</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-zinc-500">Status:</span>
              <Tabs value={statusFilter} onValueChange={setStatusFilter}>
                <TabsList>
                  <TabsTrigger value="all">All</TabsTrigger>
                  <TabsTrigger value="open">Open</TabsTrigger>
                  <TabsTrigger value="investigating">Investigating</TabsTrigger>
                  <TabsTrigger value="resolved">Resolved</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </div>

          {/* Alert List */}
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-20 rounded-lg bg-zinc-100 animate-pulse" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-zinc-400">No incidents match your filters</p>
              </CardContent>
            </Card>
          ) : (
            <ScrollArea className="h-[calc(100vh-220px)]">
              <div className="space-y-3 pr-3">
                {filtered.map((incident) => (
                  <AlertCard key={incident.incident_id} incident={incident} />
                ))}
              </div>
            </ScrollArea>
          )}
        </div>
      </main>
    </div>
  );
}

function AlertCard({ incident }: { incident: Incident }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = ENGINE_CONFIG[incident.engine];

  return (
    <Card className={incident.severity === 'critical' ? 'border-red-200' : undefined}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-4"
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Badge variant={SEVERITY_VARIANT[incident.severity] ?? 'secondary'}>
              {incident.severity.toUpperCase()}
            </Badge>
            <span className="text-xs text-zinc-400">{cfg.icon} {cfg.label}</span>
            <Badge variant={incident.status === 'resolved' ? 'success' : 'outline'} className="text-xs">
              {incident.status}
            </Badge>
          </div>
          <span className="text-xs text-zinc-400">{formatRelativeTime(incident.created_at)}</span>
        </div>
        <p className="mt-2 font-medium">{incident.title}</p>
      </button>

      {expanded && (
        <CardContent className="border-t pt-4 space-y-3">
          <div>
            <p className="text-xs font-medium text-zinc-500 mb-1">Evidence</p>
            <pre className="text-xs bg-zinc-50 rounded-md p-3 overflow-x-auto font-mono">
              {JSON.stringify(incident.evidence, null, 2)}
            </pre>
          </div>
          <div>
            <p className="text-xs font-medium text-zinc-500 mb-1">Suggested Action</p>
            <p className="text-sm">{incident.suggested_action}</p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline">Re-embed Now</Button>
            <Button size="sm" variant="outline">Run Test Suite</Button>
            <Button size="sm" variant="ghost">
              <X className="h-3.5 w-3.5 mr-1" /> Dismiss
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
