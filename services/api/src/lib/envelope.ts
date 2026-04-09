import { randomUUID } from 'node:crypto';

import type { ApiEnvelope } from '@zroky/shared-types';

function meta() {
  return {
    requestId: randomUUID(),
    timestamp: new Date().toISOString(),
    version: '2026-04-08',
  };
}

export function success<T>(data: T): ApiEnvelope<T> {
  return { success: true, data, error: null, meta: meta() };
}

export function paginated<T>(
  data: T[],
  pagination: { hasMore: boolean; nextCursor?: string },
): ApiEnvelope<T[]> {
  return { success: true, data, error: null, meta: meta(), pagination };
}

export function error(
  code: string,
  message: string,
  statusCode = 400,
): ApiEnvelope<never> & { statusCode: number } {
  return {
    success: false,
    data: null,
    error: { code, message, docUrl: `https://docs.zroky.ai/errors/${code}` },
    meta: meta(),
    statusCode,
  };
}
