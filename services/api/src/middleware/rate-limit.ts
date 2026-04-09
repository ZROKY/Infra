import type { FastifyRequest, FastifyReply } from 'fastify';

import type { AuthenticatedRequest } from './auth';
import { getRedis } from '../lib/redis';
import { error } from '../lib/envelope';

/**
 * Rate limits per tier per endpoint category (requests/minute)
 * From V1 Scope Section 7.6
 */
const RATE_LIMITS: Record<string, { ingest: number; query: number; manage: number }> = {
  free:       { ingest: 100,    query: 60,     manage: 30 },
  developer:  { ingest: 100,    query: 60,     manage: 30 },
  smb:        { ingest: 1_000,  query: 300,    manage: 100 },
  growth:     { ingest: 10_000, query: 1_000,  manage: 300 },
  enterprise: { ingest: 100_000, query: 10_000, manage: 1_000 },
};

type EndpointCategory = 'ingest' | 'query' | 'manage';

/** Determine rate limit per minute for this client's tier + endpoint category */
function getLimit(tier: string, category: EndpointCategory): number {
  const limits = RATE_LIMITS[tier] ?? RATE_LIMITS.developer!;
  return limits![category];
}

/**
 * Rate limiting middleware using Redis atomic counters
 * Uses sliding window per API key hash per minute
 */
export function rateLimit(category: EndpointCategory) {
  return async (request: FastifyRequest, reply: FastifyReply) => {
    const authReq = request as AuthenticatedRequest;
    if (!authReq.apiKey) return; // No auth = no rate limit (public endpoints)

    const redis = getRedis();
    const clientId = authReq.apiKey.clientId;

    // Get client tier from cache or default
    const configCacheKey = `client_config:${clientId}`;
    const cachedConfig = await redis.get(configCacheKey);
    const tier = cachedConfig ? JSON.parse(cachedConfig).tier : 'developer';

    const limit = getLimit(tier, category);
    const windowKey = `rate_limit:${clientId}:${category}:${Math.floor(Date.now() / 60_000)}`;

    // Atomic increment
    const current = await redis.incr(windowKey);
    if (current === 1) {
      await redis.expire(windowKey, 60);
    }

    // Set headers
    const remaining = Math.max(0, limit - current);
    const resetTime = Math.ceil(Date.now() / 60_000) * 60;
    reply.header('X-RateLimit-Limit', limit);
    reply.header('X-RateLimit-Remaining', remaining);
    reply.header('X-RateLimit-Reset', resetTime);

    if (current > limit) {
      const retryAfter = 60 - (Math.floor(Date.now() / 1_000) % 60);
      reply.header('Retry-After', retryAfter);
      return reply.status(429).send(
        error(
          'rate_limit_exceeded',
          `Rate limit exceeded. Retry after ${retryAfter} seconds.`,
          429,
        ),
      );
    }
  };
}
