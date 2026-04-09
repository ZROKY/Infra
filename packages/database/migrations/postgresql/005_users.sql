-- Migration: 005_users
-- Description: Users with Clerk auth + RBAC roles

CREATE TYPE user_role AS ENUM ('owner', 'admin', 'engineer', 'analyst', 'viewer');

CREATE TABLE IF NOT EXISTS users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  email           VARCHAR(255) NOT NULL,
  role            user_role NOT NULL DEFAULT 'viewer',
  clerk_user_id   VARCHAR(100),         -- Clerk external ID
  last_login      TIMESTAMPTZ,
  mfa_enabled     BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_email UNIQUE (email),
  CONSTRAINT uq_clerk_user UNIQUE (clerk_user_id)
);

CREATE INDEX ix_users_client ON users (client_id);
CREATE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_clerk ON users (clerk_user_id) WHERE clerk_user_id IS NOT NULL;
