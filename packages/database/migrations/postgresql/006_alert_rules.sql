-- Migration: 006_alert_rules
-- Description: Alert rules per engine per agent

CREATE TYPE alert_condition AS ENUM ('threshold', 'drift', 'anomaly');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');

CREATE TABLE IF NOT EXISTS alert_rules (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id               UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  agent_id                UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
  engine                  VARCHAR(50) NOT NULL,  -- safety, grounding, consistency, system
  condition_type          alert_condition NOT NULL DEFAULT 'threshold',
  threshold_value         NUMERIC(5,2) NOT NULL,
  notification_channels   JSONB NOT NULL DEFAULT '{"slack": true, "email": true}',
  severity                alert_severity NOT NULL DEFAULT 'medium',
  enabled                 BOOLEAN NOT NULL DEFAULT TRUE,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_alert_rules_client ON alert_rules (client_id);
CREATE INDEX ix_alert_rules_agent ON alert_rules (agent_id, engine);
