# REQUIREMENTS.md — ZROKY AI Trust Infrastructure V1

**Generated:** 2026-04-09 | **Source:** PROJECT.md + V1 Scope | **Total Requirements:** 73

## Requirement Categories

| Category | Count | Priority | REQ-IDs |
|----------|-------|----------|---------|
| Infrastructure Foundation | 7 | P0 — Build First | INFRA-01 to INFRA-07 |
| Security | 6 | P0 — Build First | SEC-01 to SEC-06 |
| API + Auth | 9 | P0 — Core Path | API-01 to API-09 |
| Safety Engine | 8 | P0 — Core Engine | SAFE-01 to SAFE-08 |
| Grounding Engine | 7 | P1 — Core Engine | GRND-01 to GRND-07 |
| Consistency Engine | 5 | P1 — Core Engine | CONS-01 to CONS-05 |
| System Engine | 7 | P1 — Core Engine | SYS-01 to SYS-07 |
| Trust Score | 4 | P0 — Core Logic | TRUST-01 to TRUST-04 |
| Dashboard | 6 | P1 — User Facing | DASH-01 to DASH-06 |
| Onboarding | 3 | P1 — User Experience | ONBOARD-01 to ONBOARD-03 |
| SDK | 3 | P1 — Developer Experience | SDK-01 to SDK-03 |
| Alerts | 2 | P2 — Enhancement | ALERT-01 to ALERT-02 |
| Integrations | 3 | P2 — Enhancement | INT-01 to INT-03 |
| Modes | 2 | P2 — Enhancement | MODE-01 to MODE-02 |
| Billing | 2 | P2 — Revenue | BILL-01 to BILL-02 |
| Viral / Growth | 4 | P2 — Growth | OSS-01, HEALTH-01, BADGE-01, FRAME-01 |

---

## P0 — Infrastructure Foundation

### INFRA-01: GKE Kubernetes Cluster
- **What:** GCP/GKE cluster provisioned via Terraform
- **Acceptance:** `kubectl get nodes` returns healthy nodes, auto-scaling configured
- **Depends on:** GCP project + billing account

### INFRA-02: PostgreSQL 15 (Cloud SQL)
- **What:** Operational database — clients, agents, API keys, subscriptions, incidents, alert rules
- **Acceptance:** All tables created, RLS policies enabled, connection from GKE verified
- **Depends on:** INFRA-01

### INFRA-03: ClickHouse (Altinity on GKE)
- **What:** Analytics database — trust_events, engine scores, Trust Score history
- **Acceptance:** ReplacingMergeTree tables created, partitioned by month + client_id, ORDER BY (client_id, agent_id, event_timestamp)
- **Depends on:** INFRA-01

### INFRA-04: Redis (Cloud Memorystore)
- **What:** Cache layer — current Trust Scores, rate limit counters, sessions, real-time scores
- **Acceptance:** Connected from GKE, sub-ms read latency verified
- **Depends on:** INFRA-01

### INFRA-05: Cloud Pub/Sub Topics
- **What:** Event queue — 4 topics (safety-events, grounding-events, consistency-events, system-events)
- **Acceptance:** All 4 topics created, test publish/subscribe successful
- **Depends on:** GCP project

### INFRA-06: Terraform IaC
- **What:** All infrastructure as code — reproducible, version-controlled
- **Acceptance:** `terraform plan` clean, `terraform apply` creates full environment
- **Depends on:** All INFRA-* requirements defined

### INFRA-07: CI/CD Pipeline
- **What:** Cloud Build + GitHub Actions — lint, test, build, deploy
- **Acceptance:** Push to main triggers automated pipeline, deploys staging → production
- **Depends on:** INFRA-01, GitHub repo

---

## P0 — Security

### SEC-01: HTTPS/TLS 1.3 + WAF
- **What:** All endpoints HTTPS-only with TLS 1.3, Cloud Armor WAF rules
- **Acceptance:** HTTP requests redirect to HTTPS, OWASP rules active, TLS 1.3 verified
- **Depends on:** INFRA-01

### SEC-02: Split API Key Hashing
- **What:** API keys stored as HMAC-SHA256 hashes, never plaintext
- **Acceptance:** Database contains only hashes, validation works via hash comparison
- **Depends on:** INFRA-02 (PostgreSQL)

### SEC-03: Encryption at Rest + Transit
- **What:** AES-256 encryption at rest (all databases), TLS 1.3 in transit (all connections)
- **Acceptance:** GCP encryption verified on all storage resources
- **Depends on:** INFRA-02, INFRA-03, INFRA-04

### SEC-04: Client Data Isolation
- **What:** ClickHouse partitioned by client_id, PostgreSQL RLS policies, every query includes client_id filter
- **Acceptance:** Automated test: create 2 clients → verify zero data leakage
- **Depends on:** INFRA-02, INFRA-03

### SEC-05: RBAC Roles
- **What:** 5 roles — Owner > Admin > Engineer > Analyst > Viewer
- **Acceptance:** Each role can only access permitted endpoints, verified via test suite
- **Depends on:** ONBOARD-02 (Clerk)

### SEC-06: Health Check Key Security
- **What:** Health Check API keys in-memory only, never persisted to database
- **Acceptance:** No Health Check keys found in any persistent storage after a health check run
- **Depends on:** HEALTH-01

---

## P0 — API + Auth

### API-01: Event Ingestion
- **What:** POST /events (single) + POST /events/batch — validate, publish to Pub/Sub
- **Acceptance:** Send event → appears in all 4 Pub/Sub topics within 500ms
- **Depends on:** INFRA-05 (Pub/Sub), SEC-02 (API keys)

### API-02: Trust Score Query
- **What:** GET /trust-score/{agent_id} — returns current Trust Score + engine breakdown
- **Acceptance:** Returns correct JSON envelope with score, status, engine details, latency < 100ms
- **Depends on:** TRUST-01, INFRA-04 (Redis cache)

### API-03: Management API
- **What:** CRUD for agents, rules, incidents — standard REST
- **Acceptance:** All CRUD operations work, proper auth checks, 404 for non-existent resources
- **Depends on:** INFRA-02 (PostgreSQL), SEC-05 (RBAC)

### API-04: Webhooks Outbound
- **What:** HMAC-signed webhook delivery with retry (3 attempts, exponential backoff)
- **Acceptance:** Configured webhook receives Trust Score alerts, signature verifiable
- **Depends on:** TRUST-01, ALERT-01

### API-05: Split API Keys
- **What:** 3 key types — ingest (zk_ingest_*), manage (zk_manage_*), agent-scoped (zk_agent_*)
- **Acceptance:** Ingest key can send events but NOT manage agents, manage key can CRUD but NOT ingest
- **Depends on:** SEC-02, INFRA-02

### API-06: Rate Limiting
- **What:** Redis atomic counters per key per tier — Developer (1K/day), Startup (10K/day), Growth (100K/day), Enterprise (custom)
- **Acceptance:** Rate limit hit returns 429 with Retry-After header, counter resets daily
- **Depends on:** INFRA-04 (Redis), BILL-02 (tiers)

### API-07: Universal Response Envelope
- **What:** All API responses wrapped in `{ success, data, error, meta }` envelope
- **Acceptance:** Every endpoint returns consistent envelope, error responses include code + message
- **Depends on:** None (code convention)

### API-08: OpenAPI Spec
- **What:** Auto-generated OpenAPI 3.1 spec from Fastify schema decorators
- **Acceptance:** /docs endpoint serves Swagger UI, spec validates cleanly
- **Depends on:** All API endpoints

### API-09: Sandbox Environment
- **What:** sandbox.ingest.zroky.ai — isolated environment with synthetic data
- **Acceptance:** Sandbox events don't touch production database, SDK works against sandbox
- **Depends on:** API-01, INFRA-01 (separate namespace)

---

## P0 — Safety Engine

### SAFE-01: Prompt Injection Detection
- **What:** 40+ pattern signatures + ML classifier for injection attempts
- **Acceptance:** Detects all OWASP Top 10 LLM injection patterns, precision > 95%
- **Depends on:** INFRA-05 (subscribes to safety-events topic)

### SAFE-02: Jailbreak Detection
- **What:** DAN patterns, roleplay tricks, encoding tricks (base64, rot13, unicode)
- **Acceptance:** Catches known jailbreak families, updates as new patterns emerge
- **Depends on:** SAFE-01 (same engine, additional module)

### SAFE-03: PII Scanning + Redaction
- **What:** guardrails-ai integration for PII detection and optional redaction
- **Acceptance:** Detects email, phone, SSN, credit card in test inputs
- **Depends on:** guardrails-ai library

### SAFE-04: Toxicity Detection
- **What:** Hate speech, profanity, threats classification
- **Acceptance:** Flags toxic content with severity score, configurable threshold per client
- **Depends on:** None (Python ML libraries)

### SAFE-05: Data Extraction Detection
- **What:** Attempts to extract system prompt, API keys, internal configs
- **Acceptance:** Detects "ignore previous instructions" variants and system prompt probes
- **Depends on:** SAFE-01 (same engine)

### SAFE-06: Campaign Detection
- **What:** 50+ similar attacks from different sources = coordinated campaign
- **Acceptance:** Groups related attacks, triggers campaign alert when threshold hit
- **Depends on:** SAFE-01, ClickHouse (historical analysis)

### SAFE-07: LLM Safety Judge
- **What:** Llama-3-8B self-hosted on Cloud Run for gray-area inputs (score 40-80)
- **Acceptance:** Judge called only for ambiguous inputs, adds explanation + adjusted score
- **Depends on:** INFRA-01 (GPU node), vLLM deployment

### SAFE-08: Attack Progression Detection
- **What:** Per-user escalation tracking — gentle probe → sophisticated attack
- **Acceptance:** Detects escalation pattern across 5+ interactions from same user
- **Depends on:** SAFE-01, Redis (session tracking)

---

## P1 — Grounding Engine

### GRND-01: RAG Retrieval Quality
- **What:** Phoenix/Arize monitoring of retrieval relevance, precision@k, recall@k
- **Acceptance:** Metrics computed on every RAG-enabled event, scores written to ClickHouse
- **Depends on:** INFRA-05, Phoenix/Arize SDK

### GRND-02: Answer-Source Consistency
- **What:** LLM-as-judge via Langfuse evaluating if answers align with retrieved sources
- **Acceptance:** Consistency score (0-1) computed, flagged when < 0.7
- **Depends on:** Langfuse integration

### GRND-03: Factual Consistency Check
- **What:** Embedding similarity between answer and source documents
- **Acceptance:** Cosine similarity computed, drift threshold configurable
- **Depends on:** Embedding model (OpenAI or local)

### GRND-04: Golden Test Set Evaluation
- **What:** Daily evaluation against client's golden test set (known correct answers)
- **Acceptance:** Scheduled job runs daily, results stored in ClickHouse, alerts on degradation
- **Depends on:** CONS-01 (shared scheduling infrastructure)

### GRND-05: Vector DB Health Monitoring
- **What:** Monitor embedding staleness, index fragmentation, query latency
- **Acceptance:** Health metrics collected hourly, alerts on degradation
- **Depends on:** Client's vector DB access (optional — clients must opt in)

### GRND-06: Claim-Level Attribution (Ragas)
- **What:** Break responses into claims, attribute each to sources, score groundedness
- **Acceptance:** `faithfulness` and `answer_relevance` scores computed per event
- **Depends on:** Ragas library + LLM evaluator

### GRND-07: Hallucination Metrics (DeepEval)
- **What:** G-Eval, SummaCon, QAG hallucination scoring
- **Acceptance:** `hallucination_score` computed per event, < 0.1 = healthy
- **Depends on:** DeepEval library

---

## P1 — Consistency Engine

### CONS-01: Daily Benchmark Testing
- **What:** lm-evaluation-harness automated runs against standard benchmarks
- **Acceptance:** Daily scores stored, trend computed over 7-day rolling window
- **Depends on:** lm-evaluation-harness + Cloud Run job

### CONS-02: Promptfoo Regression Testing
- **What:** 100 test cases per agent, run on model update/drift detection
- **Acceptance:** All test cases pass, regression flagged if pass rate drops
- **Depends on:** promptfoo library

### CONS-03: Behavioral Drift Detection
- **What:** Evidently AI — PSI, KL divergence, Wasserstein, JS distance metrics
- **Acceptance:** Drift computed on 24-hour windows, alert when any metric exceeds threshold
- **Depends on:** Evidently AI library + historical data (minimum 7 days)

### CONS-04: Behavioral Fingerprinting
- **What:** Weekly snapshot of model behavior profile (response patterns, style metrics)
- **Acceptance:** Fingerprint stored, week-over-week comparison, alert on significant change
- **Depends on:** Sufficient historical data

### CONS-05: Provider Version Tracking
- **What:** Detect when underlying model version changes (e.g., GPT-4 → GPT-4-turbo)
- **Acceptance:** Version change detected and logged, triggers re-benchmark
- **Depends on:** Model metadata in events

---

## P1 — System Engine

### SYS-01: Latency Monitoring
- **What:** P50, P95, P99 latency tracking per agent per endpoint
- **Acceptance:** Metrics computed in ClickHouse materialized view, dashboard shows trends
- **Depends on:** INFRA-03 (ClickHouse)

### SYS-02: Error Rate Tracking
- **What:** HTTP error rates, timeout rates, upstream failures
- **Acceptance:** Error rate computed per 5-minute window, alert when > threshold
- **Depends on:** INFRA-03

### SYS-03: Cost Monitoring
- **What:** Token usage tracking (prompt + completion), estimated cost per provider
- **Acceptance:** Cost visible in dashboard, daily/monthly aggregation accurate
- **Depends on:** Token count in events

### SYS-04: Uptime/Availability
- **What:** Health check every 60 seconds, uptime percentage tracking
- **Acceptance:** 99.9% uptime tracked, downtime incidents auto-generated
- **Depends on:** Scheduled health check job

### SYS-05: Throughput Monitoring
- **What:** RPS, queue depth, processing rate per engine
- **Acceptance:** Metrics in ClickHouse, dashboard panel for throughput trends
- **Depends on:** INFRA-03, INFRA-05 (Pub/Sub metrics)

### SYS-06: Cost-per-Outcome
- **What:** Not just cost per request — cost per successful outcome (user satisfaction)
- **Acceptance:** Outcome labels applied, cost-per-success computed, visible in dashboard
- **Depends on:** SYS-03, event outcome labels

### SYS-07: Performance-Quality Correlation
- **What:** Correlate latency/cost with Trust Score — find quality-performance trade-offs
- **Acceptance:** Correlation chart in Engineer view, recommendations generated
- **Depends on:** TRUST-01, SYS-01, SYS-03

---

## P0 — Trust Score

### TRUST-01: Weighted Trust Score Computation
- **What:** Formula: 0.30×Safety + 0.25×Grounding + 0.20×Consistency + 0.10×System + 0.15×Coverage
- **Acceptance:** Score matches manual calculation for test inputs, stored in ClickHouse + Redis
- **Depends on:** All 4 engines producing scores

### TRUST-02: Override Rules
- **What:** Safety floor (safety < 60 → score capped at 45), Grounding crash (grounding < 40 → max 35), Consistency decline (> 15% drop → cap at 50)
- **Acceptance:** Override triggers correctly, overridden score < formula score when triggered
- **Depends on:** TRUST-01

### TRUST-03: Cold-Start Handling
- **What:** < 10 events = no score, 10-99 = PROVISIONAL status, 100+ = STABLE
- **Acceptance:** New agent shows "Building..." with progress, PROVISIONAL label visible
- **Depends on:** TRUST-01, event counter

### TRUST-04: Status Bands
- **What:** 0-20 Critical, 21-40 Warning, 41-60 Fair, 61-80 Good, 81-100 Excellent
- **Acceptance:** Correct band label + color in API response and dashboard
- **Depends on:** TRUST-01

---

## P1 — Dashboard

### DASH-01: SMB Simplified View
- **What:** Single Trust Score + 3 panels (safety incidents, recent events, quick actions)
- **Acceptance:** Non-technical user understands AI health within 5 seconds
- **Depends on:** TRUST-01, API-02

### DASH-02: Engineer View
- **What:** 4-engine detail breakdown, incident detail, event inspector
- **Acceptance:** Engineer can diagnose Trust Score drop in under 2 minutes
- **Depends on:** All engines, API-03

### DASH-03: Executive View
- **What:** Multi-agent portfolio, trend comparisons (Growth+ tier only)
- **Acceptance:** Executive sees all agents at a glance, tier-gated correctly
- **Depends on:** TRUST-01, BILL-02 (tier check)

### DASH-04: 30-Day Trend Chart
- **What:** Recharts line chart showing Trust Score history
- **Acceptance:** Chart renders correctly, data accurate against ClickHouse query
- **Depends on:** INFRA-03 (ClickHouse historical data)

### DASH-05: Alert Center
- **What:** In-dashboard feed of recent alerts + actions taken
- **Acceptance:** Alerts appear in real-time, dismissible, filterable
- **Depends on:** ALERT-01

### DASH-06: Real-Time WebSocket
- **What:** Socket.io connection for live Trust Score updates
- **Acceptance:** Score update appears within 2 seconds of computation, reconnect on disconnect
- **Depends on:** Redis adapter for Socket.io

---

## P1 — Onboarding + SDK

### ONBOARD-01: 15-Minute Onboarding
- **What:** Signup → connect agent → see first Trust Score in under 15 minutes
- **Acceptance:** Timed test: new user completes flow in < 15 min with zero support
- **Depends on:** ONBOARD-02, ONBOARD-03, SDK-01+02

### ONBOARD-02: Clerk Auth
- **What:** Clerk integration — email/password + MFA + magic link + Google/GitHub OAuth
- **Acceptance:** All auth methods work, JWT validated by Fastify
- **Depends on:** None (Clerk SaaS)

### ONBOARD-03: Auto API Key Generation
- **What:** First login automatically generates ingest + manage API keys
- **Acceptance:** Keys visible in dashboard, copied to clipboard, SDK instructions shown
- **Depends on:** API-05

### SDK-01: Python SDK
- **What:** `pip install zroky` — event sending, score querying, decorator support
- **Acceptance:** `pip install zroky && python -c "import zroky; print(zroky.__version__)"` works
- **Depends on:** API-01, API-02

### SDK-02: Node.js SDK
- **What:** `npm install @zroky/sdk` — event sending, score querying, middleware support
- **Acceptance:** `npm install @zroky/sdk && node -e "require('@zroky/sdk')"` works
- **Depends on:** API-01, API-02

### SDK-03: Go SDK (Stub)
- **What:** Basic Go client — event sending + score query only
- **Acceptance:** `go get github.com/zroky/zroky-go` builds, basic operations work
- **Depends on:** API-01, API-02

---

## P2 — Alerts + Integrations

### ALERT-01: Email Alerts
- **What:** SendGrid email alerts — Trust Score drops, engine warnings, incidents
- **Acceptance:** Email received within 60 seconds of trigger, correct content
- **Depends on:** TRUST-01, SendGrid API key

### ALERT-02: Slack Alerts
- **What:** Slack webhook integration (Growth+ tier only)
- **Acceptance:** Slack message received, tier-gated correctly, rich formatting
- **Depends on:** TRUST-01, BILL-02

### INT-01: LangChain Callback
- **What:** ZROKYCallbackHandler for LangChain — auto-sends events
- **Acceptance:** LangChain chain runs → events appear in ZROKY dashboard
- **Depends on:** SDK-01 (Python)

### INT-02: LangGraph Wrapper
- **What:** ZROKYGraph wrapper for LangGraph nodes
- **Acceptance:** LangGraph graph execution → events with node-level granularity
- **Depends on:** SDK-01 (Python)

### INT-03: LiteLLM Proxy Reader
- **What:** Read telemetry from LiteLLM proxy mode
- **Acceptance:** LiteLLM proxy logs → ZROKY events generated
- **Depends on:** SDK-01 (Python)

### MODE-01: Monitor Mode
- **What:** Default mode — observe, score, alert. No intervention.
- **Acceptance:** Events processed, scores computed, alerts sent. No modification to AI behavior.
- **Depends on:** All engines + TRUST-01

### MODE-02: Assist Mode
- **What:** Monitor + suggestions + draft actions. Human approves.
- **Acceptance:** Suggestions generated and shown in dashboard. No auto-execution.
- **Depends on:** MODE-01, DASH-02

---

## P2 — Billing + Viral

### BILL-01: Stripe Integration
- **What:** Stripe subscriptions — plans, trials, overage handling, invoice generation
- **Acceptance:** Signup → trial → paid plan → invoice received, all automated
- **Depends on:** ONBOARD-02 (Clerk user ID maps to Stripe customer)

### BILL-02: 4 Pricing Tiers
- **What:** Developer (free, 1K events/day) → Startup ($49/mo, 10K/day) → Growth ($199/mo, 100K/day) → Enterprise (custom)
- **Acceptance:** Each tier enforced, upgrade path works, overage charging works
- **Depends on:** BILL-01

### OSS-01: Open Source Package
- **What:** Safety Engine validators + SDK on GitHub (MIT + BSL license)
- **Acceptance:** `pip install zroky-safety` works, validators usable standalone
- **Depends on:** SAFE-01–SAFE-05, SDK-01

### HEALTH-01: Free AI Health Check
- **What:** zroky.ai/scan — upload conversation → instant trust analysis, no signup
- **Acceptance:** User uploads sample → receives Trust Score breakdown in < 30 seconds
- **Depends on:** All engines (lightweight versions), Llama-3-8B judge

### BADGE-01: AI Trust Badge
- **What:** badge.zroky.ai — embeddable widget showing verified Trust Score
- **Acceptance:** Badge renders in external sites, score updates every 5 minutes, CDN-cached
- **Depends on:** TRUST-01, Redis cache

### FRAME-01: Framework Listings
- **What:** Submit to LangChain, Vercel AI SDK, OpenAI Cookbook directories
- **Acceptance:** Submissions prepared with correct format per directory requirements
- **Depends on:** SDK-01, SDK-02, INT-01–03

---

## Dependency Graph (Simplified)

```
INFRA-01 (GKE) ──► INFRA-02 (PG) ──► SEC-02 (Keys) ──► API-05 (Split Keys)
     │                  │                                       │
     ├──► INFRA-03 (CH) │                                 API-01 (Ingest)
     │         │        │                                       │
     ├──► INFRA-04 (Redis)                                INFRA-05 (Pub/Sub)
     │         │                                               │
     │    API-06 (Rate Limit)                      ┌───────────┼───────────┐
     │                                             │           │           │
     │                                         SAFE-01     GRND-01    CONS-01
     │                                            ...        ...        ...
     │                                         SAFE-08     GRND-07    CONS-05
     │                                             │           │           │
     │                                             └───────────┼───────────┘
     │                                                         │
     │                                                    TRUST-01
     │                                                         │
     │                                              ┌──────────┼──────────┐
     │                                              │          │          │
     │                                          DASH-01    ALERT-01   BADGE-01
     │                                            ...                   
     │                                          DASH-06              
     │                                              │                    
     │                                          ONBOARD-01             
     │                                              │                  
     │                                      SDK-01 + SDK-02            
     │                                              │                  
     │                                      INT-01 + INT-02 + INT-03   
     │                                              │                  
     │                                          BILL-01 + BILL-02      
     └──────────────────────────────────────────────────────────────────
```

---
*Generated: 2026-04-09 | 73 requirements across 16 categories*
