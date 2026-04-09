import type { FastifyInstance } from 'fastify';

import { requireApiKey } from '../middleware/auth';
import { success, error } from '../lib/envelope';
import {
  addSlackConfig,
  listSlackConfigs,
  updateSlackConfig,
  deleteSlackConfig,
  sendTestAlert,
  deliverAlert,
  getSlackDeliveryLog,
  type AlertPayload,
  type AlertType,
  type AlertSeverity,
} from '../lib/slack-alerts';

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const addSlackSchema = {
  type: 'object',
  required: ['webhook_url', 'channel'],
  properties: {
    webhook_url: { type: 'string', minLength: 1 },
    channel: { type: 'string', minLength: 1, maxLength: 100 },
  },
} as const;

const updateSlackSchema = {
  type: 'object',
  properties: {
    webhook_url: { type: 'string', minLength: 1 },
    channel: { type: 'string', minLength: 1, maxLength: 100 },
    enabled: { type: 'boolean' },
  },
} as const;

const triggerAlertSchema = {
  type: 'object',
  required: ['type', 'severity', 'agent_id', 'agent_name', 'title', 'message', 'current_value'],
  properties: {
    type: { type: 'string', enum: ['trust_score_drop', 'engine_threshold', 'safety_incident', 'anomaly'] },
    severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
    agent_id: { type: 'string' },
    agent_name: { type: 'string' },
    title: { type: 'string', maxLength: 200 },
    message: { type: 'string', maxLength: 2000 },
    current_value: { type: 'number' },
    threshold: { type: 'number' },
    engine: { type: 'string' },
    dashboard_url: { type: 'string' },
  },
} as const;

// ---------------------------------------------------------------------------
// Route interfaces
// ---------------------------------------------------------------------------

interface AddSlackBody {
  webhook_url: string;
  channel: string;
}

interface UpdateSlackBody {
  webhook_url?: string;
  channel?: string;
  enabled?: boolean;
}

interface TriggerAlertBody {
  type: AlertType;
  severity: AlertSeverity;
  agent_id: string;
  agent_name: string;
  title: string;
  message: string;
  current_value: number;
  threshold?: number;
  engine?: string;
  dashboard_url?: string;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function slackAlertRoutes(app: FastifyInstance) {
  /**
   * POST /v1/alerts/slack/configs
   * Add a Slack webhook configuration for an org.
   */
  app.post<{ Body: AddSlackBody }>(
    '/v1/alerts/slack/configs',
    {
      preHandler: [requireApiKey('manage')],
      schema: { body: addSlackSchema },
    },
    async (req, reply) => {
      try {
        const config = addSlackConfig(
          'org_default', // V1: single-org
          req.body.webhook_url,
          req.body.channel,
        );
        // Redact webhook URL in response (only show last 8 chars)
        const safeUrl = `...${config.webhookUrl.slice(-8)}`;
        return reply.status(201).send(
          success({
            id: config.id,
            channel: config.channel,
            webhook_url_hint: safeUrl,
            enabled: config.enabled,
            created_at: config.createdAt,
          }),
        );
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Unknown error';
        return reply.status(400).send(error('INVALID_WEBHOOK', msg));
      }
    },
  );

  /**
   * GET /v1/alerts/slack/configs
   * List all active Slack configs for the org.
   */
  app.get(
    '/v1/alerts/slack/configs',
    {
      preHandler: [requireApiKey('manage')],
    },
    async (_req, reply) => {
      const configs = listSlackConfigs('org_default');
      return reply.send(
        success(
          configs.map((c) => ({
            id: c.id,
            channel: c.channel,
            webhook_url_hint: `...${c.webhookUrl.slice(-8)}`,
            enabled: c.enabled,
            created_at: c.createdAt,
            updated_at: c.updatedAt,
          })),
        ),
      );
    },
  );

  /**
   * PATCH /v1/alerts/slack/configs/:id
   * Update a Slack config (channel, webhook URL, enabled).
   */
  app.patch<{ Params: { id: string }; Body: UpdateSlackBody }>(
    '/v1/alerts/slack/configs/:id',
    {
      preHandler: [requireApiKey('manage')],
      schema: { body: updateSlackSchema },
    },
    async (req, reply) => {
      try {
        const updated = updateSlackConfig('org_default', req.params.id, {
          webhookUrl: req.body.webhook_url,
          channel: req.body.channel,
          enabled: req.body.enabled,
        });
        if (!updated) {
          return reply.status(404).send(error('NOT_FOUND', 'Slack config not found'));
        }
        return reply.send(
          success({
            id: updated.id,
            channel: updated.channel,
            enabled: updated.enabled,
            updated_at: updated.updatedAt,
          }),
        );
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Unknown error';
        return reply.status(400).send(error('INVALID_WEBHOOK', msg));
      }
    },
  );

  /**
   * DELETE /v1/alerts/slack/configs/:id
   * Disable a Slack config.
   */
  app.delete<{ Params: { id: string } }>(
    '/v1/alerts/slack/configs/:id',
    {
      preHandler: [requireApiKey('manage')],
    },
    async (req, reply) => {
      const deleted = deleteSlackConfig('org_default', req.params.id);
      if (!deleted) {
        return reply.status(404).send(error('NOT_FOUND', 'Slack config not found'));
      }
      return reply.status(204).send();
    },
  );

  /**
   * POST /v1/alerts/slack/configs/:id/test
   * Send a test alert to verify the webhook is working.
   */
  app.post<{ Params: { id: string } }>(
    '/v1/alerts/slack/configs/:id/test',
    {
      preHandler: [requireApiKey('manage')],
    },
    async (req, reply) => {
      const result = await sendTestAlert('org_default', req.params.id);
      if (!result.success) {
        return reply.status(502).send(
          error('DELIVERY_FAILED', result.error || 'Failed to deliver test alert'),
        );
      }
      return reply.send(success({ delivered: true, attempts: result.attempts }));
    },
  );

  /**
   * POST /v1/alerts/slack/trigger
   * Trigger an alert to all configured Slack channels.
   * Used internally by engines / trust-computer or via API.
   */
  app.post<{ Body: TriggerAlertBody }>(
    '/v1/alerts/slack/trigger',
    {
      preHandler: [requireApiKey('manage', 'ingest')],
      schema: { body: triggerAlertSchema },
    },
    async (req, reply) => {
      const body = req.body;
      const alert: AlertPayload = {
        alertId: `alert_${crypto.randomUUID().replace(/-/g, '').slice(0, 16)}`,
        type: body.type,
        severity: body.severity,
        agentId: body.agent_id,
        agentName: body.agent_name,
        title: body.title,
        message: body.message,
        currentValue: body.current_value,
        threshold: body.threshold,
        engine: body.engine,
        dashboardUrl: body.dashboard_url,
        timestamp: new Date().toISOString(),
      };

      const results = await deliverAlert('org_default', alert);
      const allSuccess = results.every((r) => r.success);

      return reply.status(allSuccess ? 200 : 207).send(
        success({
          alert_id: alert.alertId,
          channels_targeted: results.length,
          channels_delivered: results.filter((r) => r.success).length,
          results: results.map((r) => ({
            config_id: r.slackConfigId,
            success: r.success,
            attempts: r.attempts,
            error: r.error,
          })),
        }),
      );
    },
  );

  /**
   * GET /v1/alerts/slack/deliveries
   * Recent delivery log for debugging.
   */
  app.get<{ Querystring: { limit?: string } }>(
    '/v1/alerts/slack/deliveries',
    {
      preHandler: [requireApiKey('manage')],
    },
    async (req, reply) => {
      const limit = parseInt(req.query.limit || '50', 10);
      const log = getSlackDeliveryLog(Math.min(limit, 200));
      return reply.send(success(log));
    },
  );
}
