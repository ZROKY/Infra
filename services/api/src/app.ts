import Fastify from 'fastify';

import { registerCors } from './plugins/cors';
import { registerSwagger } from './plugins/swagger';
import { healthRoutes } from './routes/health';

export async function buildApp() {
  const app = Fastify({
    logger: {
      level: process.env.LOG_LEVEL || 'info',
    },
  });

  // Plugins
  await registerCors(app);
  await registerSwagger(app);

  // Routes
  await app.register(healthRoutes);

  return app;
}
