-- Migration: 002_clients
-- Description: Client organizations

CREATE TYPE client_tier AS ENUM ('free', 'developer', 'smb', 'growth', 'enterprise');
CREATE TYPE client_status AS ENUM ('active', 'trial', 'suspended', 'churned');

CREATE TABLE IF NOT EXISTS clients (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                  VARCHAR(255) NOT NULL,
  plan_id               UUID NOT NULL REFERENCES subscription_plans(id),
  tier                  client_tier NOT NULL DEFAULT 'free',
  status                client_status NOT NULL DEFAULT 'active',
  slack_workspace_id    VARCHAR(100),
  slack_bot_token       TEXT,         -- AES-256-GCM encrypted at app layer
  badge_enabled         BOOLEAN NOT NULL DEFAULT FALSE,
  badge_verified_domains TEXT[] DEFAULT '{}',
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_clients_tier ON clients (tier);
CREATE INDEX ix_clients_status ON clients (status);
