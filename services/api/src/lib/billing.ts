/**
 * Stripe billing service — subscription lifecycle, checkout, webhooks.
 *
 * Uses Stripe Checkout (redirect model) for payment collection.
 * Manages trial → active → overage → cancel lifecycle.
 */

import { randomUUID } from 'node:crypto';

import type {
  TierName,
  BillingInterval,
  Subscription,
  SubscriptionStatus,
  UsageSummary,
} from './billing-types';
import { TIERS, ADDONS } from './billing-types';

// ---------------------------------------------------------------------------
// In-memory stores (V1 — replaced with DB in production)
// ---------------------------------------------------------------------------

const subscriptions = new Map<string, Subscription>();
const usageCounters = new Map<string, number>(); // key: orgId:YYYY-MM

// ---------------------------------------------------------------------------
// Subscription management
// ---------------------------------------------------------------------------

export function createSubscription(
  orgId: string,
  tier: TierName,
  interval: BillingInterval,
  stripeCustomerId: string,
  stripeSubscriptionId: string,
): Subscription {
  const now = new Date().toISOString();
  const periodEnd = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

  const tierConfig = TIERS[tier];
  const isFree = tierConfig.monthlyPrice === 0;
  const trialEnd =
    !isFree && tier !== 'enterprise'
      ? new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString()
      : null;

  const sub: Subscription = {
    id: `sub_${randomUUID().replace(/-/g, '')}`,
    orgId,
    tier,
    status: trialEnd ? 'trialing' : 'active',
    interval,
    stripeCustomerId,
    stripeSubscriptionId,
    currentPeriodStart: now,
    currentPeriodEnd: periodEnd,
    trialEnd,
    cancelAtPeriodEnd: false,
    createdAt: now,
    updatedAt: now,
  };

  subscriptions.set(orgId, sub);
  return sub;
}

export function getSubscription(orgId: string): Subscription | null {
  return subscriptions.get(orgId) || null;
}

export function updateSubscriptionStatus(
  orgId: string,
  status: SubscriptionStatus,
): Subscription | null {
  const sub = subscriptions.get(orgId);
  if (!sub) return null;
  sub.status = status;
  sub.updatedAt = new Date().toISOString();
  return sub;
}

export function changeTier(
  orgId: string,
  newTier: TierName,
  newInterval: BillingInterval,
): Subscription | null {
  const sub = subscriptions.get(orgId);
  if (!sub) return null;
  sub.tier = newTier;
  sub.interval = newInterval;
  sub.updatedAt = new Date().toISOString();
  return sub;
}

export function cancelSubscription(orgId: string, atPeriodEnd = true): Subscription | null {
  const sub = subscriptions.get(orgId);
  if (!sub) return null;
  if (atPeriodEnd) {
    sub.cancelAtPeriodEnd = true;
  } else {
    sub.status = 'canceled';
  }
  sub.updatedAt = new Date().toISOString();
  return sub;
}

// ---------------------------------------------------------------------------
// Usage metering
// ---------------------------------------------------------------------------

function usageKey(orgId: string): string {
  const period = new Date().toISOString().slice(0, 7); // YYYY-MM
  return `${orgId}:${period}`;
}

export function incrementUsage(orgId: string, count = 1): number {
  const key = usageKey(orgId);
  const current = usageCounters.get(key) || 0;
  const newCount = current + count;
  usageCounters.set(key, newCount);
  return newCount;
}

export function getUsageSummary(orgId: string): UsageSummary {
  const sub = subscriptions.get(orgId);
  const tier = sub?.tier || 'developer';
  const config = TIERS[tier];
  const key = usageKey(orgId);
  const interactions = usageCounters.get(key) || 0;
  const limit = config.interactionsPerMonth;
  const overage = limit === -1 ? 0 : Math.max(0, interactions - limit);
  const overageCost = Math.ceil((overage / 1_000) * ADDONS.additionalInteractions.pricePer1k);

  return {
    orgId,
    period: new Date().toISOString().slice(0, 7),
    tier,
    agents: 0, // resolved from agent store in production
    interactions,
    interactionLimit: limit,
    users: 0,
    userLimit: config.maxUsers,
    overageInteractions: overage,
    overageCost,
  };
}

// ---------------------------------------------------------------------------
// Tier enforcement
// ---------------------------------------------------------------------------

export function checkQuota(
  orgId: string,
  resource: 'interactions' | 'agents' | 'users',
  currentCount: number,
): { allowed: boolean; limit: number; current: number; tier: TierName } {
  const sub = subscriptions.get(orgId);
  const tier = sub?.tier || 'developer';
  const config = TIERS[tier];

  let limit: number;
  switch (resource) {
    case 'interactions':
      limit = config.interactionsPerMonth;
      break;
    case 'agents':
      limit = config.maxAgents;
      break;
    case 'users':
      limit = config.maxUsers;
      break;
  }

  return {
    allowed: limit === -1 || currentCount < limit,
    limit,
    current: currentCount,
    tier,
  };
}

// ---------------------------------------------------------------------------
// Stripe Checkout URL builder
// ---------------------------------------------------------------------------

export function buildCheckoutUrl(
  tier: TierName,
  interval: BillingInterval,
  orgId: string,
): { url: string; priceId: string } {
  const config = TIERS[tier];
  const priceId =
    interval === 'annual' ? config.stripePriceIdAnnual : config.stripePriceIdMonthly;

  // In production, this calls Stripe.checkout.sessions.create()
  // For V1, we return the price ID so the frontend can create the session
  const url = `https://checkout.stripe.com/pay?price=${priceId}&client_reference_id=${orgId}`;

  return { url, priceId };
}
