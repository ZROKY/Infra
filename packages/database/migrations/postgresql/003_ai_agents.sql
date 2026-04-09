-- Migration: 003_ai_agents
-- Description: AI agents registered per client

CREATE TYPE agent_type AS ENUM ('chatbot', 'rag', 'autonomous_agent', 'multi_agent');
CREATE TYPE integration_type AS ENUM ('sdk', 'proxy', 'webhook');

CREATE TABLE IF NOT EXISTS ai_agents (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id             UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  name                  VARCHAR(255) NOT NULL,
  type                  agent_type NOT NULL DEFAULT 'chatbot',
  provider              VARCHAR(100),       -- openai, anthropic, google, ollama
  model_name            VARCHAR(100),
  api_endpoint          TEXT,
  integration_type      integration_type NOT NULL DEFAULT 'sdk',
  trust_score_threshold INTEGER NOT NULL DEFAULT 70,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at          TIMESTAMPTZ,
  CONSTRAINT uq_agent_name_per_client UNIQUE (client_id, name)
);

CREATE INDEX ix_agents_client ON ai_agents (client_id);
CREATE INDEX ix_agents_last_seen ON ai_agents (last_seen_at DESC);
