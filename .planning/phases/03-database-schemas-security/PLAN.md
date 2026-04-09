# Phase 3: Database Schemas + Security Foundation

## Goal
PostgreSQL tables + RLS, ClickHouse tables + partitioning, Redis key structure, encryption verified

## Requirements
SEC-01, SEC-02, SEC-03, SEC-04, INFRA-02 (schema), INFRA-03 (schema)

## Success Criteria
- All PostgreSQL tables created with migrations
- RLS policies active for multi-tenant isolation
- ClickHouse trust_events table with MergeTree + monthly partitioning
- Redis key patterns documented and typed
- Multi-tenant isolation test passes (2 clients, zero data leakage)

---

## Plans

### Plan 1: PostgreSQL Migration Infrastructure (Wave 1)
- Install and configure node-pg-migrate or Drizzle ORM
- Create migration runner script
- Create base migration config

### Plan 2: PostgreSQL Core Tables (Wave 1)
- 001_subscription_plans.sql
- 002_clients.sql
- 003_ai_agents.sql
- 004_api_keys.sql
- 005_users.sql
- 006_alert_rules.sql
- 007_incidents.sql
- 008_webhook_endpoints.sql
- 009_health_check_scans.sql
- All indexes as specified in V1 Scope

### Plan 3: PostgreSQL RLS Policies (Wave 2)
- Enable RLS on all client-scoped tables
- Create policies for client_id isolation
- Create app role with restricted access
- Depends on: Plan 2

### Plan 4: ClickHouse Schema (Wave 1, parallel with Plan 2)
- trust_events table — MergeTree, PARTITION BY toYYYYMM(timestamp)
- ORDER BY (client_id, agent_id, timestamp)
- TTL 24 months
- V2 nullable columns for future backcompat

### Plan 5: Redis Key Patterns + Types (Wave 1, parallel)
- TypeScript types for all Redis key patterns
- Key builder utility with TTL constants
- 7 key patterns from V1 Scope

### Plan 6: Seed Data + Isolation Test (Wave 3)
- Dev seed script (2 test clients, agents, API keys)
- Multi-tenant isolation test
- Depends on: Plans 2, 3, 4

## Waves
- **Wave 1:** Plans 1, 2, 4, 5 (parallel)
- **Wave 2:** Plan 3 (depends on Plan 2)
- **Wave 3:** Plan 6 (depends on all)
