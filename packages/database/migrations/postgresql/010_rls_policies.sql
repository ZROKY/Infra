-- Migration: 010_rls_policies
-- Description: Row-Level Security for multi-tenant client isolation
-- All client-scoped tables get RLS policies

-- Enable RLS on all client-scoped tables
ALTER TABLE ai_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_endpoints ENABLE ROW LEVEL SECURITY;

-- Create app role (used by API server connections)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'zroky_app') THEN
    CREATE ROLE zroky_app LOGIN;
  END IF;
END
$$;

-- Grant base permissions to app role
GRANT USAGE ON SCHEMA public TO zroky_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO zroky_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO zroky_app;

-- RLS Policies: app sets current_setting('app.current_client_id') per request
-- This ensures every query is scoped to the authenticated client

-- ai_agents
CREATE POLICY agents_client_isolation ON ai_agents
  USING (client_id = current_setting('app.current_client_id')::UUID)
  WITH CHECK (client_id = current_setting('app.current_client_id')::UUID);

-- api_keys
CREATE POLICY keys_client_isolation ON api_keys
  USING (client_id = current_setting('app.current_client_id')::UUID)
  WITH CHECK (client_id = current_setting('app.current_client_id')::UUID);

-- users
CREATE POLICY users_client_isolation ON users
  USING (client_id = current_setting('app.current_client_id')::UUID)
  WITH CHECK (client_id = current_setting('app.current_client_id')::UUID);

-- alert_rules
CREATE POLICY alerts_client_isolation ON alert_rules
  USING (client_id = current_setting('app.current_client_id')::UUID)
  WITH CHECK (client_id = current_setting('app.current_client_id')::UUID);

-- incidents
CREATE POLICY incidents_client_isolation ON incidents
  USING (client_id = current_setting('app.current_client_id')::UUID)
  WITH CHECK (client_id = current_setting('app.current_client_id')::UUID);

-- webhook_endpoints
CREATE POLICY webhooks_client_isolation ON webhook_endpoints
  USING (client_id = current_setting('app.current_client_id')::UUID)
  WITH CHECK (client_id = current_setting('app.current_client_id')::UUID);

-- Superuser/migration role bypasses RLS (default behavior)
-- The app role respects RLS policies

COMMENT ON POLICY agents_client_isolation ON ai_agents IS 'Isolate agents by client_id via app.current_client_id session variable';
COMMENT ON POLICY keys_client_isolation ON api_keys IS 'Isolate API keys by client_id';
COMMENT ON POLICY users_client_isolation ON users IS 'Isolate users by client_id';
COMMENT ON POLICY alerts_client_isolation ON alert_rules IS 'Isolate alert rules by client_id';
COMMENT ON POLICY incidents_client_isolation ON incidents IS 'Isolate incidents by client_id';
COMMENT ON POLICY webhooks_client_isolation ON webhook_endpoints IS 'Isolate webhooks by client_id';
