-- Migration: 007_incidents
-- Description: Security/trust incidents

CREATE TYPE incident_status AS ENUM ('open', 'investigating', 'resolved', 'dismissed');

CREATE TABLE IF NOT EXISTS incidents (
  id                      VARCHAR(20) PRIMARY KEY,  -- INC-2026-001 format
  client_id               UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  agent_id                UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
  engine                  VARCHAR(50) NOT NULL,
  severity                alert_severity NOT NULL DEFAULT 'medium',
  title                   TEXT NOT NULL,
  description             TEXT,
  evidence                JSONB NOT NULL DEFAULT '{}',
  trust_score_at_incident NUMERIC(5,2),
  engine_score_at_incident NUMERIC(5,2),
  status                  incident_status NOT NULL DEFAULT 'open',
  assigned_to             UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at             TIMESTAMPTZ,
  resolution_notes        TEXT,
  slack_thread_ts         VARCHAR(50),
  alert_sent_slack        BOOLEAN NOT NULL DEFAULT FALSE,
  alert_sent_email        BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX ix_incidents_client_created ON incidents (client_id, created_at DESC);
CREATE INDEX ix_incidents_status ON incidents (status, severity);
CREATE INDEX ix_incidents_agent ON incidents (agent_id, created_at DESC);
