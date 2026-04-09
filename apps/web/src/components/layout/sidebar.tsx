'use client';

import { Activity, Bell, Wifi, WifiOff } from 'lucide-react';
import Link from 'next/link';

import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { useSocket } from '@/providers/socket-provider';

interface SidebarProps {
  currentPath?: string;
}

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: Activity },
  { href: '/alerts', label: 'Alert Center', icon: Bell },
];

export function Sidebar({ currentPath = '/' }: SidebarProps) {
  const { connected, alerts } = useSocket();
  const unreadAlerts = alerts.length;

  return (
    <TooltipProvider delayDuration={0}>
      <aside className="flex h-screen w-16 flex-col items-center border-r bg-white py-4">
        {/* Logo */}
        <Link href="/" className="mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zroky-600 text-white font-bold text-sm">
            Z
          </div>
        </Link>

        <Separator className="w-8 mb-4" />

        {/* Nav items */}
        <nav className="flex flex-1 flex-col items-center gap-2">
          {NAV_ITEMS.map((item) => {
            const isActive = currentPath === item.href;
            const Icon = item.icon;

            return (
              <Tooltip key={item.href}>
                <TooltipTrigger asChild>
                  <Link
                    href={item.href}
                    className={cn(
                      'relative flex h-10 w-10 items-center justify-center rounded-lg transition-colors',
                      isActive ? 'bg-zroky-50 text-zroky-700' : 'text-zinc-400 hover:bg-zinc-50 hover:text-zinc-600',
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    {item.label === 'Alert Center' && unreadAlerts > 0 && (
                      <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                        {unreadAlerts > 9 ? '9+' : unreadAlerts}
                      </span>
                    )}
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right">{item.label}</TooltipContent>
              </Tooltip>
            );
          })}
        </nav>

        {/* Connection status */}
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="mb-2">
              {connected ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-400" />
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent side="right">{connected ? 'Connected' : 'Disconnected'}</TooltipContent>
        </Tooltip>
      </aside>
    </TooltipProvider>
  );
}
