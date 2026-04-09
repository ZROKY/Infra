-- Migration: 001_subscription_plans
-- Description: Subscription plans table (referenced by clients)

CREATE TABLE IF NOT EXISTS subscription_plans (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            VARCHAR(50) UNIQUE NOT NULL,
  max_agents      INTEGER NOT NULL DEFAULT 1,
  max_interactions_month BIGINT NOT NULL DEFAULT 1000,
  max_users       INTEGER NOT NULL DEFAULT 1,
  data_retention_days INTEGER NOT NULL DEFAULT 3,
  price_monthly_usd NUMERIC(10,2) NOT NULL DEFAULT 0,
  price_annual_usd  NUMERIC(10,2) NOT NULL DEFAULT 0,
  features        JSONB NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed default plans
INSERT INTO subscription_plans (name, max_agents, max_interactions_month, max_users, data_retention_days, price_monthly_usd, price_annual_usd, features)
VALUES
  ('free',       1,    1000,    1,  3,   0,      0,      '{"health_check": true}'),
  ('developer',  3,    10000,   2,  7,   29,     290,    '{"health_check": true, "alerts": true}'),
  ('smb',        10,   100000,  5,  30,  99,     990,    '{"health_check": true, "alerts": true, "badge": true}'),
  ('growth',     50,   1000000, 20, 90,  299,    2990,   '{"health_check": true, "alerts": true, "badge": true, "custom_thresholds": true}'),
  ('enterprise', -1,   -1,      -1, 365, 0,      0,      '{"health_check": true, "alerts": true, "badge": true, "custom_thresholds": true, "sla": true, "dedicated_support": true}')
ON CONFLICT (name) DO NOTHING;
