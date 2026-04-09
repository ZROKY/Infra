import type { FastifyInstance } from 'fastify';

import { success, error } from '../lib/envelope';
import { getRedis } from '../lib/redis';

export async function badgeRoutes(app: FastifyInstance) {
  // GET /v1/badge/:agentId — Public badge score (no auth, cached 30s)
  app.get<{ Params: { agentId: string } }>(
    '/v1/badge/:agentId',
    {
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
      const { agentId } = request.params;
      const redis = getRedis();
      const cached = await redis.get(`badge_score:${agentId}`);

      if (!cached) {
        return reply.status(404).send(
          error('not_found', 'Badge not found or not enabled for this agent', 404),
        );
      }

      const badge = JSON.parse(cached);
      reply.header('Cache-Control', 'public, max-age=30');
      return reply.send(success(badge));
    },
  );
}
