'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Sidebar } from '@/components/layout/sidebar';
import { ViewSwitcher, type DashboardView } from '@/components/layout/view-switcher';
import { EngineerView } from '@/components/views/engineer-view';
import { ExecutiveView } from '@/components/views/executive-view';
import { SmBView } from '@/components/views/smb-view';

// Default agent ID for single-agent view — replaced by URL param or context in production
const DEFAULT_AGENT_ID = 'default';

export default function DashboardPage() {
  const router = useRouter();
  const [view, setView] = useState<DashboardView>('smb');
  const [selectedAgentId, setSelectedAgentId] = useState(DEFAULT_AGENT_ID);

  const handleAgentClick = (agentId: string) => {
    setSelectedAgentId(agentId);
    setView('engineer');
  };

  return (
    <div className="flex h-screen">
      <Sidebar currentPath="/" />

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-7xl px-6 py-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold">Dashboard</h1>
              <p className="text-sm text-zinc-500">Monitor AI agent trust in real-time</p>
            </div>
            <ViewSwitcher value={view} onChange={setView} />
          </div>

          {/* View Content */}
          {view === 'smb' && (
            <SmBView
              agentId={selectedAgentId}
              onViewAlerts={() => router.push('/alerts')}
              onSwitchToEngineer={() => setView('engineer')}
            />
          )}
          {view === 'engineer' && (
            <EngineerView agentId={selectedAgentId} />
          )}
          {view === 'executive' && (
            <ExecutiveView onAgentClick={handleAgentClick} />
          )}
        </div>
      </main>
    </div>
  );
}
