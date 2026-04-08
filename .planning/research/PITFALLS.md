# Pitfalls Research — ZROKY AI Trust Infrastructure

**Researched:** 2026-04-09 | **Source:** V1 Scope Document + Industry Analysis

## Critical Pitfalls

### 1. Engine Cold Start — Trust Score Unreliability Early On
- **Warning signs:** New clients see wildly fluctuating Trust Scores in first 24 hours. Support tickets about "broken" scores.
- **Why it happens:** Engines need sufficient data to produce meaningful scores. 10 events ≠ statistical significance.
- **Prevention strategy:** 
  - V1 Scope already addresses this: < 10 events = no score, 10-99 = PROVISIONAL, 100+ = STABLE
  - Add clear UI messaging: "Building your Trust Score... 47/100 events collected"
  - Progress bar on dashboard during cold-start phase
- **Phase to address:** Dashboard phase (onboarding UX)

### 2. ClickHouse Query Performance Degradation
- **Warning signs:** Dashboard load time increasing as data grows. Trust Score computation taking > 1 second.
- **Why it happens:** Bad partitioning strategy, missing ORDER BY in table definition, or querying without time bounds.
- **Prevention strategy:**
  - Partition by `toYYYYMM(event_timestamp)` from Day 1
  - ORDER BY `(client_id, agent_id, event_timestamp)` — not generic
  - Always include time bounds in queries (`WHERE event_timestamp > now() - INTERVAL 24 HOUR`)
  - Materialized views for Trust Score aggregation (avoid real-time full-table scans)
- **Phase to address:** Database schema phase

### 3. Pub/Sub Message Ordering and Deduplication
- **Warning signs:** Trust Score computed from out-of-order events. Duplicate scoring.
- **Why it happens:** Cloud Pub/Sub does NOT guarantee ordering. Messages can be delivered more than once.
- **Prevention strategy:**
  - Include `event_id` (UUID) + `event_timestamp` in every message
  - Engine workers use ClickHouse's `ReplacingMergeTree` to handle duplicates
  - Trust Score Computer uses time-window aggregation (not individual events)
  - Idempotent processing in all engine workers
- **Phase to address:** Event ingestion + engine worker phases

### 4. WebSocket Connection Scaling
- **Warning signs:** Dashboard becomes slow/unresponsive when multiple team members are connected. Connection drops during deployments.
- **Why it happens:** WebSocket connections are stateful. Kubernetes pod restarts kill all connections. No sticky sessions.
- **Prevention strategy:**
  - Redis adapter for Socket.io (shared state across pods)
  - Graceful shutdown: notify clients before pod termination
  - Client-side auto-reconnect with exponential backoff (Socket.io has this built-in)
  - Consider SSE (Server-Sent Events) for Trust Score updates — simpler, stateless
- **Phase to address:** Dashboard phase

### 5. Multi-Tenant Data Isolation Failure
- **Warning signs:** Client A sees Client B's data. API key from one org works on another's agents.
- **Why it happens:** Missing `client_id` filter in queries. Shared database without row-level security.
- **Prevention strategy:**
  - EVERY query must include `WHERE client_id = ?` — enforce via middleware/ORM wrapper
  - API key validation returns `client_id` — inject into every downstream call
  - ClickHouse: partition by client_id (secondary partition after month)
  - PostgreSQL: Row-Level Security (RLS) policies
  - Automated test: create 2 test clients, verify zero data leakage
- **Phase to address:** API + database phases (CRITICAL — bake in from Day 1)

### 6. Safety Engine False Positives
- **Warning signs:** Legitimate user inputs flagged as attacks. Trust Score drops for benign conversations. Client complaints about "broken safety detection."
- **Why it happens:** Pattern matching is aggressive. ML classifier not tuned for domain-specific language. Medical/legal/financial terms trigger toxicity detectors.
- **Prevention strategy:**
  - LLM Safety Judge (Llama-3-8B) as second-pass for gray-area inputs (scores 40-80)
  - Per-client sensitivity tuning (configurable thresholds)
  - Allow clients to whitelist domain-specific terms
  - Provide "dispute" mechanism in dashboard (client marks false positive → improves model)
- **Phase to address:** Safety Engine phase

### 7. API Key Leakage in Client Applications
- **Warning signs:** API keys appearing in client-side JavaScript, GitHub repos, or logs.
- **Why it happens:** Ingest keys designed for backend use get embedded in frontend code.
- **Prevention strategy:**
  - Clear documentation: "NEVER put ingest keys in frontend code"
  - Separate key types with clear naming: `zk_ingest_*` (backend), `zk_public_*` (badge only)
  - Key rotation workflow in dashboard
  - Health Check keys: in-memory only, never persisted (already in V1 Scope)
- **Phase to address:** API + SDK documentation phases

### 8. Trust Score Gaming
- **Warning signs:** Clients only send "good" interactions to ZROKY. Coverage score doesn't catch selective sending.
- **Why it happens:** When clients learn that bad interactions lower Trust Score, incentive to filter.
- **Prevention strategy:**
  - Coverage Score (15% weight) penalizes selective sending
  - Compare `events_received / expected_events` (7-day rolling average)
  - Statistical anomaly detection: sudden drops in event volume = suspicious
  - Badge shows coverage score — low coverage = visible warning
- **Phase to address:** Trust Score computation phase

### 9. LLM-as-Judge Reliability
- **Warning signs:** Langfuse/Ragas evaluators give inconsistent scores for same input. Hallucination detection misses obvious cases.
- **Why it happens:** LLM judges are themselves non-deterministic. Temperature, prompt phrasing, model version changes affect results.
- **Prevention strategy:**
  - Set temperature=0 for all judge calls
  - Use structured output (JSON mode) for scoring
  - Run 3 judge passes and take majority vote for critical decisions (not every request — only escalated ones)
  - Cache judge results for identical inputs (deterministic deduplication)
  - Monitor judge consistency as a meta-metric
- **Phase to address:** Grounding Engine phase

### 10. Cost Explosion from Engine Processing
- **Warning signs:** GCP bill spikes unexpectedly. Safety Judge (Llama-3-8B) GPU costs dominate.
- **Why it happens:** Every event triggers all 4 engines. High-volume clients = high compute.
- **Prevention strategy:**
  - Safety Judge only called for flagged inputs (score 40-80), not every request
  - Batch processing for non-real-time engines (Consistency, Grounding golden tests)
  - Tier-based rate limits (Developer: 10K events/day, Enterprise: unlimited but priced)
  - ClickHouse materialized views reduce query cost
  - Auto-scaling engine workers with max replica limits
- **Phase to address:** Infrastructure + billing phases

## Pitfall Priority Matrix

| Pitfall | Severity | Likelihood | Phase to Prevent |
|---------|----------|------------|-----------------|
| Multi-tenant isolation | CRITICAL | MEDIUM | Database/API (Day 1) |
| ClickHouse query perf | HIGH | HIGH | Database schema |
| Pub/Sub ordering | HIGH | HIGH | Event ingestion |
| Safety false positives | HIGH | MEDIUM | Safety Engine |
| Trust Score gaming | MEDIUM | HIGH | Trust Score computation |
| Cold start UX | MEDIUM | HIGH | Dashboard/onboarding |
| WebSocket scaling | MEDIUM | MEDIUM | Dashboard |
| API key leakage | MEDIUM | MEDIUM | SDK/docs |
| LLM judge reliability | MEDIUM | MEDIUM | Grounding Engine |
| Cost explosion | MEDIUM | LOW (if tiered) | Infrastructure/billing |

---
*Generated: 2026-04-09*
