import { createHmac } from 'node:crypto';

import type { FastifyRequest, FastifyReply } from 'fastify';

import { config } from '../config';
import { getPool } from '../lib/db';
import { getRedis } from '../lib/redis';
import { error } from '../lib/envelope';

export type ApiKeyType = 'ingest' | 'manage' | 'agent';

interface CachedApiKey {
  clientId: string;
  keyType: ApiKeyType;
  scopes: string[];
  agentId: string | null;
}

const KEY_CACHE_TTL = 300; // 5 minutes

function hashKey(rawKey: string): string {
  return createHmac('sha256', config.apiKeyHmacSecret).update(rawKey).digest('hex');
}

async function lookupKey(keyHash: string): Promise<CachedApiKey | null> {
  const redis = getRedis();
  const cacheKey = `api_key_cache:${keyHash}`;

  // Check Redis cache first
  const cached = await redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  // Fallback to PostgreSQL
  const pool = getPool();
  const { rows } = await pool.query(
    `SELECT client_id, key_type, scopes, agent_id
     FROM api_keys
     WHERE key_hash = $1
       AND revoked_at IS NULL
       AND (expires_at IS NULL OR expires_at > NOW())`,
    [keyHash],
  );

  if (rows.length === 0) return null;

  const row = rows[0];
  const keyData: CachedApiKey = {
    clientId: row.client_id,
    keyType: row.key_type,
    scopes: row.scopes || [],
    agentId: row.agent_id,
  };

  // Cache in Redis
  await redis.set(cacheKey, JSON.stringify(keyData), 'EX', KEY_CACHE_TTL);

  // Update last_used_at (fire and forget)
  pool.query('UPDATE api_keys SET last_used_at = NOW() WHERE key_hash = $1', [keyHash]).catch(() => {});

  return keyData;
}

/** Fastify preHandler: validate Bearer API key + enforce key type */
export function requireApiKey(...allowedTypes: ApiKeyType[]) {
  return async (request: FastifyRequest, reply: FastifyReply) => {
    const authHeader = request.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return reply.status(401).send(
        error('unauthorized', 'Missing or invalid Authorization header', 401),
      );
    }

    const rawKey = authHeader.slice(7);
    if (!rawKey || rawKey.length < 20) {
      return reply.status(401).send(
        error('unauthorized', 'Invalid API key format', 401),
      );
    }

    const keyHash = hashKey(rawKey);
    const keyData = await lookupKey(keyHash);

    if (!keyData) {
      return reply.status(401).send(
        error('unauthorized', 'Invalid or expired API key', 401),
      );
    }

    // Check key type
    if (allowedTypes.length > 0 && !allowedTypes.includes(keyData.keyType)) {
      return reply.status(403).send(
        error(
          'forbidden',
          `This endpoint requires a ${allowedTypes.join(' or ')} key. Your key is type: ${keyData.keyType}`,
          403,
        ),
      );
    }

    // Attach to request for downstream use
    (request as AuthenticatedRequest).apiKey = keyData;
  };
}

export interface AuthenticatedRequest extends FastifyRequest {
  apiKey: CachedApiKey;
}
