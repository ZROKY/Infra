import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import type { FastifyInstance } from 'fastify';

export async function registerSwagger(app: FastifyInstance) {
  await app.register(swagger, {
    openapi: {
      openapi: '3.1.0',
      info: {
        title: 'ZROKY API',
        description: 'AI Trust Infrastructure Platform API',
        version: '1.0.0',
      },
      servers: [
        { url: 'http://localhost:4000', description: 'Local' },
        { url: 'https://api.zroky.ai', description: 'Production' },
      ],
    },
  });

  await app.register(swaggerUi, {
    routePrefix: '/docs',
  });
}
