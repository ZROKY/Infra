-- Migration: 004_api_keys
-- Description: Split API keys with HMAC-SHA256 hashing

CREATE TYPE api_key_type AS ENUM ('ingest', 'manage', 'agent');

CREATE TABLE IF NOT EXISTS api_keys (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  key_hash        VARCHAR(64) NOT NULL,     -- HMAC-SHA256 hash, raw key NEVER stored
  key_prefix      VARCHAR(12) NOT NULL,     -- First 12 chars shown in dashboard
  key_type        api_key_type NOT NULL,
  scopes          TEXT[] NOT NULL DEFAULT '{}',
  agent_id        UUID REFERENCES ai_agents(id) ON DELETE CASCADE, -- Only for 'agent' type keys
  last_used_at    TIMESTAMPTZ,
  expires_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  revoked_at      TIMESTAMPTZ,
  CONSTRAINT uq_key_hash UNIQUE (key_hash)
);

CREATE INDEX ix_api_keys_client ON api_keys (client_id);
CREATE INDEX ix_api_keys_hash ON api_keys (key_hash) WHERE revoked_at IS NULL;
CREATE INDEX ix_api_keys_prefix ON api_keys (key_prefix);

-- Max 5 active keys per client
-- Enforced at app layer, not DB constraint (to allow temporary overlap during rotation)
COMMENT ON TABLE api_keys IS 'Split API keys: zk_ingest_*, zk_manage_*, zk_agent_*. Max 5 active per client. 24h grace period on rotation.';
