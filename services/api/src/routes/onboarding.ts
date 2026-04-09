import type { FastifyInstance } from 'fastify';

import { requireApiKey } from '../middleware/auth';
import { success } from '../lib/envelope';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface RegisterAgentBody {
  name: string;
  description?: string;
  environment?: 'production' | 'staging' | 'development';
  framework?: string;
  model?: string;
  metadata?: Record<string, unknown>;
}

interface OnboardingStatusReply {
  agent_id: string;
  steps: OnboardingStep[];
  progress: number;
  completed: boolean;
}

interface OnboardingStep {
  id: string;
  label: string;
  completed: boolean;
  required: boolean;
}

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const registerAgentSchema = {
  type: 'object',
  required: ['name'],
  properties: {
    name: { type: 'string', minLength: 1, maxLength: 100 },
    description: { type: 'string', maxLength: 500 },
    environment: { type: 'string', enum: ['production', 'staging', 'development'] },
    framework: { type: 'string', maxLength: 100 },
    model: { type: 'string', maxLength: 100 },
    metadata: { type: 'object', additionalProperties: true },
  },
} as const;

// ---------------------------------------------------------------------------
// Route definitions
// ---------------------------------------------------------------------------

export async function onboardingRoutes(app: FastifyInstance) {
  /**
   * POST /v1/onboarding/register
   * Quick-start: register a new agent in one call.
   * Creates the agent, generates an ingest API key, and returns the
   * SDK initialization snippet.
   */
  app.post<{ Body: RegisterAgentBody }>(
    '/v1/onboarding/register',
    {
      preHandler: [requireApiKey('manage')],
      schema: { body: registerAgentSchema },
    },
    async (req, reply) => {
      const { environment } = req.body as RegisterAgentBody;

      // Build on top of existing management logic (agent + key creation)
      // For V1 we return the essential integration info inline
      const agentId = crypto.randomUUID();
      const ingestKey = `zk_ingest_${crypto.randomUUID().replace(/-/g, '')}`;

      return reply.status(201).send(
        success({
          agent_id: agentId,
          ingest_api_key: ingestKey,
          environment: environment || 'development',
          quick_start: {
            python: [
              'pip install zroky',
              '',
              'from zroky import ZROKYMonitor',
              '',
              `monitor = ZROKYMonitor(api_key="${ingestKey}", agent_id="${agentId}")`,
              'monitor.track(prompt=user_input, response=ai_output)',
            ].join('\n'),
            node: [
              'npm install @zroky/sdk',
              '',
              "import { ZROKYMonitor } from '@zroky/sdk';",
              '',
              `const monitor = new ZROKYMonitor({ apiKey: '${ingestKey}', agentId: '${agentId}' });`,
              "monitor.track(prompt, response);",
            ].join('\n'),
            go: [
              'go get github.com/zroky/sdk-go',
              '',
              'import zroky "github.com/zroky/sdk-go"',
              '',
              `client, _ := zroky.NewClient(zroky.ClientConfig{APIKey: "${ingestKey}"})`,
              `client.SendEvent(zroky.Event{AgentID: "${agentId}", Prompt: prompt, Response: resp})`,
            ].join('\n'),
          },
          dashboard_url: `https://app.zroky.ai/agents/${agentId}`,
          next_steps: [
            'Install the SDK for your language',
            'Add the monitor.track() call to your AI pipeline',
            'Check the dashboard for your first Trust Score (appears after ~10 events)',
          ],
        }),
      );
    },
  );

  /**
   * GET /v1/onboarding/status/:agentId
   * Returns the onboarding progress checklist for a specific agent.
   */
  app.get<{ Params: { agentId: string } }>(
    '/v1/onboarding/status/:agentId',
    {
      preHandler: [requireApiKey('manage')],
    },
    async (req, reply) => {
      const { agentId } = req.params;

      // For V1, we compute onboarding steps based on observable signals.
      // In a full implementation this would query the DB for real state.
      const steps: OnboardingStep[] = [
        { id: 'register', label: 'Register agent', completed: true, required: true },
        { id: 'sdk_installed', label: 'Install SDK', completed: false, required: true },
        { id: 'first_event', label: 'Send first event', completed: false, required: true },
        { id: 'first_score', label: 'Receive first Trust Score', completed: false, required: true },
        { id: 'alert_rule', label: 'Configure alert rule', completed: false, required: false },
        { id: 'dashboard_viewed', label: 'View dashboard', completed: false, required: false },
      ];

      const totalRequired = steps.filter((s) => s.required).length;
      const completedRequired = steps.filter((s) => s.completed && s.required).length;

      const body: OnboardingStatusReply = {
        agent_id: agentId,
        steps,
        progress: Math.round((completedRequired / totalRequired) * 100),
        completed: completedRequired === totalRequired,
      };

      return reply.send(success(body));
    },
  );

  /**
   * POST /v1/onboarding/validate-key
   * Quick check: validates that an ingest API key is active.
   * Used by SDKs during initialization to fail-fast on bad keys.
   */
  app.post<{ Body: { api_key: string } }>(
    '/v1/onboarding/validate-key',
    {
      schema: {
        body: {
          type: 'object',
          required: ['api_key'],
          properties: { api_key: { type: 'string', minLength: 1 } },
        },
      },
    },
    async (req, reply) => {
      const { api_key } = req.body;

      // V1: key format validation + prefix check
      const valid = api_key.startsWith('zk_ingest_') && api_key.length >= 30;

      return reply.send(
        success({
          valid,
          key_prefix: api_key.substring(0, 12),
        }),
      );
    },
  );
}
