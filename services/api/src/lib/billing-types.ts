/**
 * Billing types — Pricing tiers, subscription lifecycle, and Stripe mappings.
 */

// ---------------------------------------------------------------------------
// Tiers
// ---------------------------------------------------------------------------

export type TierName = 'developer' | 'smb' | 'growth' | 'enterprise';

export interface TierConfig {
  name: TierName;
  displayName: string;
  monthlyPrice: number; // cents (0 = free)
  annualPrice: number; // cents per month
  maxAgents: number; // -1 = unlimited
  interactionsPerMonth: number; // -1 = unlimited
  maxUsers: number; // -1 = unlimited
  dataRetentionDays: number;
  features: string[];
  stripePriceIdMonthly: string;
  stripePriceIdAnnual: string;
}

export const TIERS: Record<TierName, TierConfig> = {
  developer: {
    name: 'developer',
    displayName: 'Developer',
    monthlyPrice: 0,
    annualPrice: 0,
    maxAgents: 1,
    interactionsPerMonth: 10_000,
    maxUsers: 3,
    dataRetentionDays: 3,
    features: ['email_alerts', 'smb_dashboard', 'community_support'],
    stripePriceIdMonthly: '',
    stripePriceIdAnnual: '',
  },
  smb: {
    name: 'smb',
    displayName: 'SMB',
    monthlyPrice: 9_900,
    annualPrice: 7_900,
    maxAgents: 1,
    interactionsPerMonth: 500_000,
    maxUsers: 5,
    dataRetentionDays: 7,
    features: [
      'email_alerts',
      'smb_dashboard',
      'standard_support',
      'badge',
      'health_check',
    ],
    stripePriceIdMonthly: process.env.STRIPE_SMB_MONTHLY_PRICE_ID || '',
    stripePriceIdAnnual: process.env.STRIPE_SMB_ANNUAL_PRICE_ID || '',
  },
  growth: {
    name: 'growth',
    displayName: 'Growth',
    monthlyPrice: 49_900,
    annualPrice: 39_900,
    maxAgents: 5,
    interactionsPerMonth: 5_000_000,
    maxUsers: 20,
    dataRetentionDays: 90,
    features: [
      'email_alerts',
      'slack_alerts',
      'full_dashboard',
      'api_webhooks',
      'priority_support',
      'badge',
      'health_check',
    ],
    stripePriceIdMonthly: process.env.STRIPE_GROWTH_MONTHLY_PRICE_ID || '',
    stripePriceIdAnnual: process.env.STRIPE_GROWTH_ANNUAL_PRICE_ID || '',
  },
  enterprise: {
    name: 'enterprise',
    displayName: 'Enterprise',
    monthlyPrice: -1, // custom
    annualPrice: -1,
    maxAgents: -1,
    interactionsPerMonth: -1,
    maxUsers: -1,
    dataRetentionDays: 730,
    features: [
      'all_alerts',
      'full_dashboard',
      'custom_dashboard',
      'compliance_mode',
      'sso',
      'sla_99_9',
      'dedicated_onboarding',
      'api_webhooks',
    ],
    stripePriceIdMonthly: '',
    stripePriceIdAnnual: '',
  },
};

// ---------------------------------------------------------------------------
// Add-ons
// ---------------------------------------------------------------------------

export const ADDONS = {
  additionalAgent: { pricePerMonth: 5_000, unit: 'agent' }, // $50/agent/mo
  additionalInteractions: { pricePer1k: 1, unit: '1,000 interactions' }, // $0.001/1K
  complianceReportPack: { pricePerMonth: 20_000, unit: 'pack' }, // $200/mo
} as const;

// ---------------------------------------------------------------------------
// Subscription
// ---------------------------------------------------------------------------

export type SubscriptionStatus =
  | 'trialing'
  | 'active'
  | 'past_due'
  | 'canceled'
  | 'unpaid'
  | 'paused';

export type BillingInterval = 'monthly' | 'annual';

export interface Subscription {
  id: string;
  orgId: string;
  tier: TierName;
  status: SubscriptionStatus;
  interval: BillingInterval;
  stripeCustomerId: string;
  stripeSubscriptionId: string;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  trialEnd: string | null;
  cancelAtPeriodEnd: boolean;
  createdAt: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Usage Metering
// ---------------------------------------------------------------------------

export interface UsageSummary {
  orgId: string;
  period: string; // YYYY-MM
  tier: TierName;
  agents: number;
  interactions: number;
  interactionLimit: number;
  users: number;
  userLimit: number;
  overageInteractions: number;
  overageCost: number; // cents
}

// ---------------------------------------------------------------------------
// Webhook Events
// ---------------------------------------------------------------------------

export type WebhookEventType =
  | 'incident.created'
  | 'incident.resolved'
  | 'trust_score.changed'
  | 'trust_score.critical'
  | 'safety.campaign_detected';

export interface WebhookConfig {
  id: string;
  orgId: string;
  url: string;
  secret: string;
  events: WebhookEventType[];
  active: boolean;
  createdAt: string;
}

export interface WebhookDelivery {
  id: string;
  webhookId: string;
  eventType: WebhookEventType;
  payload: Record<string, unknown>;
  statusCode: number | null;
  attempt: number;
  deliveredAt: string | null;
  error: string | null;
}
