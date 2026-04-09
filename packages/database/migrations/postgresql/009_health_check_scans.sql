-- Migration: 009_health_check_scans
-- Description: Free health check scan records

CREATE TYPE scan_type AS ENUM ('api_endpoint', 'api_key', 'csv_upload');

CREATE TABLE IF NOT EXISTS health_check_scans (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email                   VARCHAR(255),                 -- Nullable for first anonymous scan
  user_id                 UUID REFERENCES users(id) ON DELETE SET NULL,
  ip_hash                 VARCHAR(64) NOT NULL,         -- Hashed IP, NOT raw IP
  scan_type               scan_type NOT NULL,
  overall_score           NUMERIC(5,2),
  safety_score            NUMERIC(5,2),
  accuracy_score          NUMERIC(5,2),
  consistency_score       NUMERIC(5,2),
  findings_count          INTEGER NOT NULL DEFAULT 0,
  critical_findings_count INTEGER NOT NULL DEFAULT 0,
  report_url              TEXT,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at              TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '30 days'
);

CREATE INDEX ix_scans_ip_created ON health_check_scans (ip_hash, created_at DESC);
CREATE INDEX ix_scans_email ON health_check_scans (email) WHERE email IS NOT NULL;
