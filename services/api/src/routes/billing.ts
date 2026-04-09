import type { FastifyInstance } from 'fastify';

import { requireApiKey } from '../middleware/auth';
import { success, error } from '../lib/envelope';
import {
  createSubscription,
  getSubscription,
  updateSubscriptionStatus,
  changeTier,
  cancelSubscription,
  getUsageSummary,
  checkQuota,
  buildCheckoutUrl,
} from '../lib/billing';
import type { TierName, BillingInterval, SubscriptionStatus } from '../lib/billing-types';
import { TIERS } from '../lib/billing-types';

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const checkoutSchema = {
  type: 'object',
  required: ['tier', 'interval'],
  properties: {
    tier: { type: 'string', enum: ['developer', 'smb', 'growth', 'enterprise'] },
    interval: { type: 'string', enum: ['monthly', 'annual'] },
  },
} as const;

const changeTierSchema = {
  type: 'object',
  required: ['tier', 'interval'],
  properties: {
    tier: { type: 'string', enum: ['developer', 'smb', 'growth', 'enterprise'] },
    interval: { type: 'string', enum: ['monthly', 'annual'] },
  },
} as const;

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function billingRoutes(app: FastifyInstance) {
  /**
   * GET /v1/billing/tiers
   * List all available pricing tiers (public).
   */
  app.get('/v1/billing/tiers', async (_req, reply) => {
    const tiers = Object.values(TIERS).map((t) => ({
      name: t.name,
      display_name: t.displayName,
      monthly_price: t.monthlyPrice,
      annual_price: t.annualPrice,
      max_agents: t.maxAgents,
      interactions_per_month: t.interactionsPerMonth,
      max_users: t.maxUsers,
      data_retention_days: t.dataRetentionDays,
      features: t.features,
    }));
    return reply.send(success(tiers));
  });

  /**
   * POST /v1/billing/checkout
   * Create a Stripe checkout session URL.
   */
  app.post<{ Body: { tier: TierName; interval: BillingInterval } }>(
    '/v1/billing/checkout',
    {
      preHandler: [requireApiKey('manage')],
      schema: { body: checkoutSchema },
    },
    async (req, reply) => {
      const { tier, interval } = req.body;
      if (tier === 'developer') {
        return reply.status(400).send(error('INVALID_TIER', 'Developer tier is free, no checkout needed'));
      }
      if (tier === 'enterprise') {
        return reply.status(400).send(
          error('CONTACT_SALES', 'Enterprise tier requires contacting sales@zroky.ai'),
        );
      }

      const result = buildCheckoutUrl(tier, interval, 'org_default');
      return reply.send(success({ checkout_url: result.url, price_id: result.priceId }));
    },
  );

  /**
   * GET /v1/billing/subscription
   * Get current subscription for the org.
   */
  app.get(
    '/v1/billing/subscription',
    {
      preHandler: [requireApiKey('manage')],
    },
    async (_req, reply) => {
      const sub = getSubscription('org_default');
      if (!sub) {
        return reply.send(
          success({
            tier: 'developer',
            status: 'active',
            message: 'Free tier — no active paid subscription',
          }),
        );
      }
      return reply.send(success(sub));
    },
  );

  /**
   * POST /v1/billing/subscription
   * Create a subscription (called after Stripe checkout success).
   */
  app.post<{
    Body: {
      tier: TierName;
      interval: BillingInterval;
      stripe_customer_id: string;
      stripe_subscription_id: string;
    };
  }>(
    '/v1/billing/subscription',
    {
      preHandler: [requireApiKey('manage')],
      schema: {
        body: {
          type: 'object',
          required: ['tier', 'interval', 'stripe_customer_id', 'stripe_subscription_id'],
          properties: {
            tier: { type: 'string', enum: ['developer', 'smb', 'growth', 'enterprise'] },
            interval: { type: 'string', enum: ['monthly', 'annual'] },
            stripe_customer_id: { type: 'string', minLength: 1 },
            stripe_subscription_id: { type: 'string', minLength: 1 },
          },
        },
      },
    },
    async (req, reply) => {
      const { tier, interval, stripe_customer_id, stripe_subscription_id } = req.body;
      const sub = createSubscription(
        'org_default',
        tier,
        interval,
        stripe_customer_id,
        stripe_subscription_id,
      );
      return reply.status(201).send(success(sub));
    },
  );

  /**
   * PATCH /v1/billing/subscription/tier
   * Change subscription tier.
   */
  app.patch<{ Body: { tier: TierName; interval: BillingInterval } }>(
    '/v1/billing/subscription/tier',
    {
      preHandler: [requireApiKey('manage')],
      schema: { body: changeTierSchema },
    },
    async (req, reply) => {
      const { tier, interval } = req.body;
      const updated = changeTier('org_default', tier, interval);
      if (!updated) {
        return reply.status(404).send(error('NOT_FOUND', 'No active subscription'));
      }
      return reply.send(success(updated));
    },
  );

  /**
   * POST /v1/billing/subscription/cancel
   * Cancel subscription (at period end by default).
   */
  app.post<{ Body: { immediate?: boolean } }>(
    '/v1/billing/subscription/cancel',
    {
      preHandler: [requireApiKey('manage')],
      schema: {
        body: {
          type: 'object',
          properties: { immediate: { type: 'boolean' } },
        },
      },
    },
    async (req, reply) => {
      const immediate = req.body?.immediate ?? false;
      const sub = cancelSubscription('org_default', !immediate);
      if (!sub) {
        return reply.status(404).send(error('NOT_FOUND', 'No active subscription'));
      }
      return reply.send(success(sub));
    },
  );

  /**
   * GET /v1/billing/usage
   * Get current billing period usage summary.
   */
  app.get(
    '/v1/billing/usage',
    {
      preHandler: [requireApiKey('manage')],
    },
    async (_req, reply) => {
      const usage = getUsageSummary('org_default');
      return reply.send(success(usage));
    },
  );

  /**
   * POST /v1/billing/quota-check
   * Check if org is within quota for a resource.
   */
  app.post<{ Body: { resource: 'interactions' | 'agents' | 'users'; current_count: number } }>(
    '/v1/billing/quota-check',
    {
      preHandler: [requireApiKey('manage', 'ingest')],
      schema: {
        body: {
          type: 'object',
          required: ['resource', 'current_count'],
          properties: {
            resource: { type: 'string', enum: ['interactions', 'agents', 'users'] },
            current_count: { type: 'number', minimum: 0 },
          },
        },
      },
    },
    async (req, reply) => {
      const { resource, current_count } = req.body;
      const result = checkQuota('org_default', resource, current_count);
      return reply.send(success(result));
    },
  );

  /**
   * POST /v1/billing/webhooks/stripe
   * Stripe webhook receiver (signature validation in production).
   */
  app.post<{ Body: Record<string, unknown> }>(
    '/v1/billing/webhooks/stripe',
    async (req, reply) => {
      const event = req.body as { type?: string; data?: { object?: Record<string, unknown> } };
      const eventType = event.type;

      if (!eventType) {
        return reply.status(400).send(error('INVALID_EVENT', 'Missing event type'));
      }

      // Handle Stripe lifecycle events
      switch (eventType) {
        case 'customer.subscription.updated': {
          const status = event.data?.object?.status as SubscriptionStatus | undefined;
          if (status) {
            updateSubscriptionStatus('org_default', status);
          }
          break;
        }
        case 'customer.subscription.deleted':
          updateSubscriptionStatus('org_default', 'canceled');
          break;
        case 'invoice.payment_failed':
          updateSubscriptionStatus('org_default', 'past_due');
          break;
        case 'invoice.paid':
          updateSubscriptionStatus('org_default', 'active');
          break;
        default:
          // Log unknown event, don't fail
          break;
      }

      return reply.status(200).send(success({ received: true }));
    },
  );
}
