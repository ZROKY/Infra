import { randomUUID } from 'node:crypto';

import type { FastifyInstance } from 'fastify';

import { requireApiKey, type AuthenticatedRequest } from '../middleware/auth';
import { rateLimit } from '../middleware/rate-limit';
import { success, error } from '../lib/envelope';
import { publishToAllEngines } from '../lib/pubsub';

interface EventBody {
  agent_id: string;
  prompt: string;
  response: string;
  model?: string;
  metadata?: Record<string, unknown>;
  session_id?: string;
}

interface BatchBody {
  events: EventBody[];
}

const eventBodySchema = {
  type: 'object',
  required: ['agent_id', 'prompt', 'response'],
  properties: {
    agent_id: { type: 'string', format: 'uuid' },
    prompt: { type: 'string', minLength: 1, maxLength: 50_000 },
    response: { type: 'string', minLength: 1, maxLength: 50_000 },
    model: { type: 'string', maxLength: 100 },
    metadata: { type: 'object', additionalProperties: true },
    session_id: { type: 'string', maxLength: 255 },
  },
} as const;

export async function eventRoutes(app: FastifyInstance) {
  // POST /v1/events — Single event ingestion
  app.post<{ Body: EventBody }>(
    '/v1/events',
    {
      preHandler: [requireApiKey('ingest', 'agent'), rateLimit('ingest')],
      schema: {
        body: eventBodySchema,
        response: {
          202: {
            type: 'object',
            properties: {
              success: { type: 'boolean' },
              data: {
                type: 'object',
                properties: {
                  event_id: { type: 'string' },
                  status: { type: 'string' },
                },
              },
              error: { type: 'null' },
              meta: { type: 'object' },
            },
          },
        },
      },
    },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const body = request.body;

      // If agent-scoped key, enforce agent_id match
      if (apiKey.keyType === 'agent' && apiKey.agentId && apiKey.agentId !== body.agent_id) {
        return reply.status(403).send(
          error('forbidden', 'Agent-scoped key can only ingest events for its assigned agent', 403),
        );
      }

      const eventId = `evt_${randomUUID().replace(/-/g, '')}`;
      const idempotencyKey = request.headers['idempotency-key'] as string | undefined;

      const eventPayload = {
        event_id: eventId,
        client_id: apiKey.clientId,
        agent_id: body.agent_id,
        prompt: body.prompt,
        response: body.response,
        model: body.model || '',
        metadata: body.metadata || {},
        session_id: body.session_id || '',
        timestamp: new Date().toISOString(),
        idempotency_key: idempotencyKey || null,
      };

      // Publish to all 4 engine topics (async — sub-10ms response)
      publishToAllEngines(eventPayload, {
        client_id: apiKey.clientId,
        agent_id: body.agent_id,
        event_id: eventId,
      }).catch((err) => {
        request.log.error({ err, eventId }, 'Failed to publish event to Pub/Sub');
      });

      return reply.status(202).send(
        success({ event_id: eventId, status: 'accepted' }),
      );
    },
  );

  // POST /v1/events/batch — Batch event ingestion (up to 1,000)
  app.post<{ Body: BatchBody }>(
    '/v1/events/batch',
    {
      preHandler: [requireApiKey('ingest', 'agent'), rateLimit('ingest')],
      schema: {
        body: {
          type: 'object',
          required: ['events'],
          properties: {
            events: {
              type: 'array',
              items: eventBodySchema,
              minItems: 1,
              maxItems: 1_000,
            },
          },
        },
      },
    },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const { events } = request.body;

      const accepted: string[] = [];
      const errors: Array<{ index: number; error: string }> = [];

      const publishPromises = events.map(async (event, index) => {
        // Validate agent-scoped key
        if (apiKey.keyType === 'agent' && apiKey.agentId && apiKey.agentId !== event.agent_id) {
          errors.push({ index, error: 'Agent-scoped key mismatch' });
          return;
        }

        const eventId = `evt_${randomUUID().replace(/-/g, '')}`;
        const payload = {
          event_id: eventId,
          client_id: apiKey.clientId,
          agent_id: event.agent_id,
          prompt: event.prompt,
          response: event.response,
          model: event.model || '',
          metadata: event.metadata || {},
          session_id: event.session_id || '',
          timestamp: new Date().toISOString(),
        };

        try {
          await publishToAllEngines(payload, {
            client_id: apiKey.clientId,
            agent_id: event.agent_id,
            event_id: eventId,
          });
          accepted.push(eventId);
        } catch {
          errors.push({ index, error: 'Publish failed' });
        }
      });

      await Promise.all(publishPromises);

      return reply.status(202).send(
        success({
          accepted: accepted.length,
          rejected: errors.length,
          event_ids: accepted,
          errors: errors.length > 0 ? errors : undefined,
        }),
      );
    },
  );
}
