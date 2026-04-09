import type { FastifyInstance } from 'fastify';

import { success } from '../lib/envelope';

export async function healthRoutes(app: FastifyInstance) {
  app.get(
    '/health',
    {
      schema: {
        tags: ['System'],
        summary: 'Health check',
        response: {
          200: {
            type: 'object',
            properties: {
              success: { type: 'boolean' },
              data: {
                type: 'object',
                properties: {
                  status: { type: 'string' },
                  version: { type: 'string' },
                  uptime: { type: 'number' },
                },
              },
              error: { type: 'null' },
              meta: {
                type: 'object',
                properties: {
                  requestId: { type: 'string' },
                  timestamp: { type: 'string' },
                },
              },
            },
          },
        },
      },
    },
    async () => {
      return success({
        status: 'ok',
        version: '1.0.0',
        uptime: process.uptime(),
      });
    },
  );
}
