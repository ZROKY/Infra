import type { Metadata } from 'next';

import './globals.css';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'ZROKY — AI Trust Infrastructure',
  description: 'Monitor, score, and certify AI agent behavior in production.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-zinc-50 font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
