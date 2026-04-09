-- Migration: 008_webhook_endpoints
-- Description: Webhook endpoints for event delivery

CREATE TABLE IF NOT EXISTS webhook_endpoints (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  url             TEXT NOT NULL,
  secret          VARCHAR(64) NOT NULL,     -- HMAC signing secret
  events          TEXT[] NOT NULL DEFAULT '{}',  -- incident.created, trust_score.changed, etc.
  enabled         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_webhooks_client ON webhook_endpoints (client_id);
CREATE INDEX ix_webhooks_enabled ON webhook_endpoints (enabled) WHERE enabled = TRUE;
