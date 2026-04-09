import type { FastifyInstance } from 'fastify';

import { requireApiKey } from '../middleware/auth';
import { success } from '../lib/envelope';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type OperatingMode = 'monitor' | 'assist';

interface ModeInfo {
  agent_id: string;
  mode: OperatingMode;
  description: string;
  features: string[];
}

// ---------------------------------------------------------------------------
// In-memory store (V1 — replaced with DB in production)
// ---------------------------------------------------------------------------

const agentModes = new Map<string, OperatingMode>();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getModeInfo(agentId: string): ModeInfo {
  const mode = agentModes.get(agentId) || 'monitor';

  if (mode === 'monitor') {
    return {
      agent_id: agentId,
      mode: 'monitor',
      description:
        'Observe-only mode. ZROKY collects telemetry and computes Trust Scores without affecting AI behavior.',
      features: [
        'Event ingestion',
        'Trust Score computation',
        'Dashboard visibility',
        'Alert notifications',
      ],
    };
  }

  return {
    agent_id: agentId,
    mode: 'assist',
    description:
      'Advisory mode. In addition to monitoring, ZROKY surfaces suggestions in the Engineer view (never auto-blocks).',
    features: [
      'All Monitor features',
      'Inline suggestions in Engineer view',
      'Response improvement hints',
      'Safety recommendation nudges',
    ],
  };
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function modeRoutes(app: FastifyInstance) {
  /**
   * GET /v1/agents/:agentId/mode
   * Returns the current operating mode for an agent.
   */
  app.get<{ Params: { agentId: string } }>(
    '/v1/agents/:agentId/mode',
    {
      preHandler: [requireApiKey('manage')],
    },
    async (req, reply) => {
      const { agentId } = req.params;
      return reply.send(success(getModeInfo(agentId)));
    },
  );

  /**
   * PUT /v1/agents/:agentId/mode
   * Switch the operating mode for an agent.
   */
  app.put<{ Params: { agentId: string }; Body: { mode: OperatingMode } }>(
    '/v1/agents/:agentId/mode',
    {
      preHandler: [requireApiKey('manage')],
      schema: {
        body: {
          type: 'object',
          required: ['mode'],
          properties: {
            mode: { type: 'string', enum: ['monitor', 'assist'] },
          },
        },
      },
    },
    async (req, reply) => {
      const { agentId } = req.params;
      const { mode } = req.body;

      agentModes.set(agentId, mode);

      return reply.send(
        success({
          ...getModeInfo(agentId),
          changed: true,
        }),
      );
    },
  );

  /**
   * GET /v1/agents/:agentId/suggestions
   * Returns active suggestions for an agent (only in assist mode).
   * In monitor mode, returns an empty array.
   */
  app.get<{ Params: { agentId: string } }>(
    '/v1/agents/:agentId/suggestions',
    {
      preHandler: [requireApiKey('manage')],
    },
    async (req, reply) => {
      const { agentId } = req.params;
      const mode = agentModes.get(agentId) || 'monitor';

      if (mode === 'monitor') {
        return reply.send(
          success({
            agent_id: agentId,
            mode: 'monitor',
            suggestions: [],
            message: 'No suggestions in monitor mode. Switch to assist mode to enable.',
          }),
        );
      }

      // V1: Return placeholder suggestions structure.
      // In production, these come from the engine analysis pipeline.
      return reply.send(
        success({
          agent_id: agentId,
          mode: 'assist',
          suggestions: [],
          message: 'Suggestions are generated after sufficient event data is collected.',
        }),
      );
    },
  );
}
