'use client';

import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

export type DashboardView = 'smb' | 'engineer' | 'executive';

interface ViewSwitcherProps {
  value: DashboardView;
  onChange: (view: DashboardView) => void;
  executiveEnabled?: boolean;
}

export function ViewSwitcher({ value, onChange, executiveEnabled = true }: ViewSwitcherProps) {
  return (
    <Tabs value={value} onValueChange={(v) => onChange(v as DashboardView)}>
      <TabsList>
        <TabsTrigger value="smb">Overview</TabsTrigger>
        <TabsTrigger value="engineer">Engineer</TabsTrigger>
        <TabsTrigger value="executive" disabled={!executiveEnabled}>
          Executive{!executiveEnabled && ' 🔒'}
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
