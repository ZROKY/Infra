import Fastify from 'fastify';

import { registerCors } from './plugins/cors';
import { registerSwagger } from './plugins/swagger';
import { healthRoutes } from './routes/health';
import { eventRoutes } from './routes/events';
import { trustScoreRoutes } from './routes/trust-score';
import { agentRoutes, alertRuleRoutes, apiKeyRoutes, incidentRoutes } from './routes/management';
import { badgeRoutes } from './routes/badge';
import { onboardingRoutes } from './routes/onboarding';
import { modeRoutes } from './routes/modes';
import { slackAlertRoutes } from './routes/slack-alerts';
import { billingRoutes } from './routes/billing';
import { healthCheckRoutes } from './routes/health-check';
import { sandboxRoutes } from './routes/sandbox';

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
  await app.register(eventRoutes);
  await app.register(trustScoreRoutes);
  await app.register(agentRoutes);
  await app.register(alertRuleRoutes);
  await app.register(apiKeyRoutes);
  await app.register(incidentRoutes);
  await app.register(badgeRoutes);
  await app.register(onboardingRoutes);
  await app.register(modeRoutes);
  await app.register(slackAlertRoutes);
  await app.register(billingRoutes);
  await app.register(healthCheckRoutes);
  await app.register(sandboxRoutes);

  return app;
}
