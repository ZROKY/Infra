import type { FastifyInstance } from 'fastify';

import { requireApiKey, type AuthenticatedRequest } from '../middleware/auth';
import { rateLimit } from '../middleware/rate-limit';
import { success, error } from '../lib/envelope';
import { getRedis } from '../lib/redis';

export async function trustScoreRoutes(app: FastifyInstance) {
  // GET /v1/trust-score/:agentId — Current trust score from Redis
  app.get<{ Params: { agentId: string } }>(
    '/v1/trust-score/:agentId',
    {
      preHandler: [requireApiKey('manage', 'agent'), rateLimit('query')],
      schema: {
        params: {
          type: 'object',
          required: ['agentId'],
          properties: {
            agentId: { type: 'string', format: 'uuid' },
          },
        },
      },
    },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const { agentId } = request.params;

      // Agent-scoped key can only query its own agent
      if (apiKey.keyType === 'agent' && apiKey.agentId && apiKey.agentId !== agentId) {
        return reply.status(403).send(
          error('forbidden', 'Agent-scoped key can only query its assigned agent', 403),
        );
      }

      const redis = getRedis();
      const scoreKey = `trust_score:${apiKey.clientId}:${agentId}`;
      const cached = await redis.get(scoreKey);

      if (!cached) {
        return reply.status(404).send(
          error('not_found', 'No trust score available for this agent. Send events first.', 404),
        );
      }

      const score = JSON.parse(cached);
      return reply.send(success(score));
    },
  );

  // GET /v1/trust-score/:agentId/history — Score history from ClickHouse (TODO: Phase 8)
  app.get<{ Params: { agentId: string }; Querystring: { period?: string } }>(
    '/v1/trust-score/:agentId/history',
    {
      preHandler: [requireApiKey('manage', 'agent'), rateLimit('query')],
      schema: {
        params: {
          type: 'object',
          required: ['agentId'],
          properties: {
            agentId: { type: 'string', format: 'uuid' },
          },
        },
        querystring: {
          type: 'object',
          properties: {
            period: { type: 'string', enum: ['1h', '24h', '7d', '30d'], default: '24h' },
          },
        },
      },
    },
    async (request, reply) => {
      // Placeholder — ClickHouse query will be added in Phase 8 (Dashboard)
      return reply.send(
        success({
          agent_id: request.params.agentId,
          period: request.query.period || '24h',
          data_points: [],
          message: 'History endpoint available after Trust Computer is implemented (Phase 8)',
        }),
      );
    },
  );
}
