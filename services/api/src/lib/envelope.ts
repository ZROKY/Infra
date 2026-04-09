import { randomUUID } from 'node:crypto';

import type { ApiEnvelope } from '@zroky/shared-types';

export function success<T>(data: T): ApiEnvelope<T> {
  return {
    success: true,
    data,
    error: null,
    meta: {
      requestId: randomUUID(),
      timestamp: new Date().toISOString(),
    },
  };
}

export function error(code: string, message: string): ApiEnvelope<never> {
  return {
    success: false,
    data: null,
    error: { code, message },
    meta: {
      requestId: randomUUID(),
      timestamp: new Date().toISOString(),
    },
  };
}
