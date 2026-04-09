import type { FastifyInstance } from 'fastify';

import { success } from '../lib/envelope';

// ---------------------------------------------------------------------------
// Sandbox environment — API-09
// Isolated namespace: sandbox.ingest.zroky.ai
// Events don't touch production. SDK works against sandbox.
// ---------------------------------------------------------------------------

interface SandboxEvent {
  id: string;
  agent_id: string;
  prompt: string;
  response: string;
  model: string;
  timestamp: string;
}

// In-memory sandbox store (never touches production DB)
const sandboxEvents: SandboxEvent[] = [];
const MAX_SANDBOX_EVENTS = 1_000;

export async function sandboxRoutes(app: FastifyInstance) {
  /**
   * POST /v1/sandbox/events
   * Ingest events into sandbox (isolated from production).
   */
  app.post<{
    Body: {
      agent_id: string;
      prompt: string;
      response: string;
      model?: string;
    };
  }>(
    '/v1/sandbox/events',
    {
      schema: {
        body: {
          type: 'object',
          required: ['agent_id', 'prompt', 'response'],
          properties: {
            agent_id: { type: 'string' },
            prompt: { type: 'string', minLength: 1, maxLength: 50_000 },
            response: { type: 'string', minLength: 1, maxLength: 50_000 },
            model: { type: 'string', maxLength: 100 },
          },
        },
      },
    },
    async (req, reply) => {
      const event: SandboxEvent = {
        id: `sbx_${crypto.randomUUID().replace(/-/g, '').slice(0, 16)}`,
        agent_id: req.body.agent_id,
        prompt: req.body.prompt,
        response: req.body.response,
        model: req.body.model || '',
        timestamp: new Date().toISOString(),
      };

      // Ring buffer — drop oldest when full
      if (sandboxEvents.length >= MAX_SANDBOX_EVENTS) {
        sandboxEvents.shift();
      }
      sandboxEvents.push(event);

      return reply.status(202).send(
        success({
          event_id: event.id,
          environment: 'sandbox',
          message: 'Event accepted (sandbox — not processed by production engines)',
        }),
      );
    },
  );

  /**
   * POST /v1/sandbox/events/batch
   * Batch sandbox ingest (up to 100 events).
   */
  app.post<{
    Body: {
      events: Array<{
        agent_id: string;
        prompt: string;
        response: string;
        model?: string;
      }>;
    };
  }>(
    '/v1/sandbox/events/batch',
    {
      schema: {
        body: {
          type: 'object',
          required: ['events'],
          properties: {
            events: {
              type: 'array',
              maxItems: 100,
              items: {
                type: 'object',
                required: ['agent_id', 'prompt', 'response'],
                properties: {
                  agent_id: { type: 'string' },
                  prompt: { type: 'string', minLength: 1, maxLength: 50_000 },
                  response: { type: 'string', minLength: 1, maxLength: 50_000 },
                  model: { type: 'string', maxLength: 100 },
                },
              },
            },
          },
        },
      },
    },
    async (req, reply) => {
      const ids: string[] = [];

      for (const evt of req.body.events) {
        const event: SandboxEvent = {
          id: `sbx_${crypto.randomUUID().replace(/-/g, '').slice(0, 16)}`,
          agent_id: evt.agent_id,
          prompt: evt.prompt,
          response: evt.response,
          model: evt.model || '',
          timestamp: new Date().toISOString(),
        };
        if (sandboxEvents.length >= MAX_SANDBOX_EVENTS) {
          sandboxEvents.shift();
        }
        sandboxEvents.push(event);
        ids.push(event.id);
      }

      return reply.status(202).send(
        success({
          accepted: ids.length,
          environment: 'sandbox',
          event_ids: ids,
        }),
      );
    },
  );

  /**
   * GET /v1/sandbox/events
   * List recent sandbox events (for debugging).
   */
  app.get<{ Querystring: { agent_id?: string; limit?: string } }>(
    '/v1/sandbox/events',
    async (req, reply) => {
      const limit = Math.min(parseInt(req.query.limit || '50', 10), 200);
      let events = sandboxEvents;

      if (req.query.agent_id) {
        events = events.filter((e) => e.agent_id === req.query.agent_id);
      }

      return reply.send(
        success({
          environment: 'sandbox',
          total: events.length,
          events: events.slice(-limit),
        }),
      );
    },
  );

  /**
   * DELETE /v1/sandbox/events
   * Clear all sandbox events.
   */
  app.delete('/v1/sandbox/events', async (_req, reply) => {
    const count = sandboxEvents.length;
    sandboxEvents.length = 0;
    return reply.send(success({ cleared: count, environment: 'sandbox' }));
  });

  /**
   * GET /v1/sandbox/info
   * Sandbox environment info.
   */
  app.get('/v1/sandbox/info', async (_req, reply) => {
    return reply.send(
      success({
        environment: 'sandbox',
        description: 'Isolated sandbox — events are NOT processed by production engines',
        max_events: MAX_SANDBOX_EVENTS,
        current_events: sandboxEvents.length,
        endpoints: {
          ingest: 'POST /v1/sandbox/events',
          batch: 'POST /v1/sandbox/events/batch',
          list: 'GET /v1/sandbox/events',
          clear: 'DELETE /v1/sandbox/events',
        },
      }),
    );
  });
}
