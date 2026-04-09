import type { FastifyInstance } from 'fastify';

import { success, error } from '../lib/envelope';
import {
  createSessionKey,
  validateSessionKey,
  revokeSessionKey,
  runHealthCheck,
  type ConversationTurn,
} from '../lib/health-check';

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const scanSchema = {
  type: 'object',
  required: ['conversation'],
  properties: {
    conversation: {
      type: 'array',
      minItems: 1,
      maxItems: 100,
      items: {
        type: 'object',
        required: ['role', 'content'],
        properties: {
          role: { type: 'string', enum: ['user', 'assistant', 'system'] },
          content: { type: 'string', minLength: 1, maxLength: 50_000 },
        },
      },
    },
    model: { type: 'string', maxLength: 100 },
  },
} as const;

// ---------------------------------------------------------------------------
// Routes — All public (no auth required)
// ---------------------------------------------------------------------------

export async function healthCheckRoutes(app: FastifyInstance) {
  /**
   * POST /v1/health-check/session
   * Create a temporary session key for the scan widget.
   * Keys are in-memory only (SEC-06). Rate limited by IP.
   */
  app.post('/v1/health-check/session', async (_req, reply) => {
    const key = createSessionKey();
    return reply.status(201).send(
      success({
        session_key: key,
        expires_in: 900, // 15 minutes
        message: 'Use this key in the X-Health-Check-Key header for scan requests',
      }),
    );
  });

  /**
   * POST /v1/health-check/scan
   * Run a free AI trust analysis on a conversation.
   * No signup required — paste a conversation and get instant results.
   */
  app.post<{ Body: { conversation: ConversationTurn[]; model?: string } }>(
    '/v1/health-check/scan',
    {
      schema: { body: scanSchema },
    },
    async (req, reply) => {
      const sessionKey = req.headers['x-health-check-key'] as string | undefined;
      if (sessionKey && !validateSessionKey(sessionKey)) {
        return reply.status(401).send(error('EXPIRED_SESSION', 'Session key expired or invalid'));
      }

      const { conversation, model } = req.body;

      // Validate conversation has at least one user and one assistant turn
      const hasUser = conversation.some((t) => t.role === 'user');
      const hasAssistant = conversation.some((t) => t.role === 'assistant');

      if (!hasUser || !hasAssistant) {
        return reply.status(400).send(
          error(
            'INVALID_CONVERSATION',
            'Conversation must include at least one user and one assistant message',
          ),
        );
      }

      const result = runHealthCheck({ conversation, model });

      // Revoke session key after use (one-time)
      if (sessionKey) {
        revokeSessionKey(sessionKey);
      }

      return reply.send(success(result));
    },
  );

  /**
   * POST /v1/health-check/scan/csv
   * Upload CSV format: role,content per row.
   */
  app.post<{ Body: { csv: string; model?: string } }>(
    '/v1/health-check/scan/csv',
    {
      schema: {
        body: {
          type: 'object',
          required: ['csv'],
          properties: {
            csv: { type: 'string', minLength: 1, maxLength: 500_000 },
            model: { type: 'string', maxLength: 100 },
          },
        },
      },
    },
    async (req, reply) => {
      const { csv, model } = req.body;

      // Parse CSV: role,content
      const lines = csv.split('\n').filter((l) => l.trim());
      const conversation: ConversationTurn[] = [];

      for (const line of lines) {
        const firstComma = line.indexOf(',');
        if (firstComma === -1) continue;

        const role = line.slice(0, firstComma).trim().toLowerCase();
        const content = line.slice(firstComma + 1).trim();

        if (['user', 'assistant', 'system'].includes(role) && content) {
          conversation.push({ role: role as ConversationTurn['role'], content });
        }
      }

      if (conversation.length === 0) {
        return reply.status(400).send(
          error('INVALID_CSV', 'No valid conversation turns found. Format: role,content'),
        );
      }

      const result = runHealthCheck({ conversation, model });
      return reply.send(success(result));
    },
  );
}
