'use client';

import type { ReactNode } from 'react';
import { SWRConfig } from 'swr';

import { SocketProvider } from '@/providers/socket-provider';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <SWRConfig value={{ revalidateOnFocus: false }}>
      <SocketProvider>{children}</SocketProvider>
    </SWRConfig>
  );
}
