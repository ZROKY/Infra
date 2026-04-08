# ZROKY — AI Trust Infrastructure Platform

## What This Is

ZROKY is an AI Trust Infrastructure Platform that monitors, scores, and certifies AI agent behavior in production. It provides a unified Trust Score (0-100) computed from 4 specialized engines (Safety, Grounding, Consistency, System), with real-time dashboards, alerts, SDKs, and an embeddable Trust Badge. The target audience is developers and companies running AI agents who need to answer: "Can I trust my AI?"

## Core Value

A developer signs up, connects their AI agent via SDK in under 15 minutes, sees a live Trust Score on a dashboard, and gets alerts when something goes wrong. If this flow doesn't work flawlessly, nothing else matters.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Engines:**
- [ ] SAFE-01: Safety Engine — prompt injection detection (40+ signatures + ML classifier)
- [ ] SAFE-02: Safety Engine — jailbreak detection (DAN, roleplay, encoding tricks)
- [ ] SAFE-03: Safety Engine — PII scanning + redaction (guardrails-ai)
- [ ] SAFE-04: Safety Engine — toxicity detection (hate, profanity, threats)
- [ ] SAFE-05: Safety Engine — data extraction detection (system prompt, API keys)
- [ ] SAFE-06: Safety Engine — campaign detection (50+ similar attacks = coordinated)
- [ ] SAFE-07: Safety Engine — LLM Safety Judge (Llama-3-8B for subtle attacks)
- [ ] SAFE-08: Safety Engine — attack progression detection (per-user escalation tracking)
- [ ] GRND-01: Grounding Engine — RAG retrieval quality monitoring (Phoenix/Arize)
- [ ] GRND-02: Grounding Engine — answer-source consistency (LLM-as-judge via Langfuse)
- [ ] GRND-03: Grounding Engine — factual consistency check (embedding similarity)
- [ ] GRND-04: Grounding Engine — golden test set evaluation (daily)
- [ ] GRND-05: Grounding Engine — vector DB health monitoring
- [ ] GRND-06: Grounding Engine — claim-level attribution (Ragas)
- [ ] GRND-07: Grounding Engine — hallucination metrics (DeepEval)
- [ ] CONS-01: Consistency Engine — daily benchmark testing (lm-evaluation-harness)
- [ ] CONS-02: Consistency Engine — promptfoo regression testing (100 test cases)
- [ ] CONS-03: Consistency Engine — behavioral drift detection (Evidently AI — PSI, KL, Wasserstein, JS)
- [ ] CONS-04: Consistency Engine — behavioral fingerprinting (weekly)
- [ ] CONS-05: Consistency Engine — provider version tracking
- [ ] SYS-01: System Engine — latency monitoring (P50, P95, P99)
- [ ] SYS-02: System Engine — error rate tracking (HTTP errors, timeouts)
- [ ] SYS-03: System Engine — cost monitoring (token usage, estimated cost)
- [ ] SYS-04: System Engine — uptime/availability (health check every 60s)
- [ ] SYS-05: System Engine — throughput (RPS, queue depth)
- [ ] SYS-06: System Engine — cost-per-outcome intelligence
- [ ] SYS-07: System Engine — performance-quality correlation

**Trust Score:**
- [ ] TRUST-01: 4-engine weighted Trust Score computation (30/25/20/10/15)
- [ ] TRUST-02: Override rules (safety floor, grounding crash, consistency decline)
- [ ] TRUST-03: Cold-start handling (< 10 events = no score, 10-99 = provisional)
- [ ] TRUST-04: Trust Score status bands (Critical/Warning/Fair/Good/Excellent)

**API:**
- [ ] API-01: Event ingestion endpoint (POST /events — single + batch)
- [ ] API-02: Trust Score query (GET /trust-score/{agent_id})
- [ ] API-03: Management API (agents, rules, incidents CRUD)
- [ ] API-04: Webhooks outbound (HMAC-signed delivery + retry)
- [ ] API-05: Split API keys (ingest vs manage vs agent-scoped)
- [ ] API-06: Rate limiting (Redis atomic counters, per key, per tier)
- [ ] API-07: Universal response envelope on all endpoints
- [ ] API-08: OpenAPI spec auto-generation
- [ ] API-09: Sandbox environment (sandbox.ingest.zroky.ai)

**Dashboard:**
- [ ] DASH-01: SMB Simplified View (Trust Score + 3 panels)
- [ ] DASH-02: Engineer View (4-engine detail + incident detail)
- [ ] DASH-03: Executive View (multi-agent portfolio, Growth+ only)
- [ ] DASH-04: Trust Score 30-day trend chart (Recharts)
- [ ] DASH-05: Alert Center (in-dashboard feed)
- [ ] DASH-06: Real-time WebSocket updates (Socket.io)

**Onboarding:**
- [ ] ONBOARD-01: Signup → connect → first Trust Score in under 15 minutes
- [ ] ONBOARD-02: Clerk auth integration (email/password + MFA + magic link)
- [ ] ONBOARD-03: API key generation on first login

**SDK:**
- [ ] SDK-01: Python SDK (pip install zroky)
- [ ] SDK-02: Node.js SDK (npm install @zroky/sdk)
- [ ] SDK-03: Go SDK (stub — basic client only)

**Alerts:**
- [ ] ALERT-01: Email alerts via SendGrid (all tiers)
- [ ] ALERT-02: Slack alerts via webhook (Growth+ only)

**Integrations:**
- [ ] INT-01: LangChain ZROKYCallbackHandler
- [ ] INT-02: LangGraph ZROKYGraph wrapper
- [ ] INT-03: LiteLLM proxy mode telemetry reader

**Modes:**
- [ ] MODE-01: Monitor Mode (observe + score + alert, no intervention)
- [ ] MODE-02: Assist Mode (monitor + suggestions + draft actions)

**Viral / Growth:**
- [ ] OSS-01: Open-source SDK + Safety Engine validators (GitHub, MIT + BSL)
- [ ] HEALTH-01: Free AI Health Check (zroky.ai/scan — no signup required)
- [ ] BADGE-01: AI Trust Badge (badge.zroky.ai — embeddable widget)
- [ ] FRAME-01: Framework listings submitted (LangChain, Vercel AI SDK, OpenAI Cookbook)

**Billing:**
- [ ] BILL-01: Stripe integration (plans + trial + overage handling)
- [ ] BILL-02: 4 pricing tiers (Developer free → Enterprise)

**Infrastructure:**
- [ ] INFRA-01: GCP/GKE Kubernetes cluster
- [ ] INFRA-02: PostgreSQL 15 (Cloud SQL) — operational data
- [ ] INFRA-03: ClickHouse (Altinity on GKE) — analytics data
- [ ] INFRA-04: Redis (Cloud Memorystore) — cache
- [ ] INFRA-05: Cloud Pub/Sub — event queue (1 topic per engine)
- [ ] INFRA-06: Terraform IaC for all resources
- [ ] INFRA-07: CI/CD pipeline (Cloud Build + GitHub Actions)

**Security:**
- [ ] SEC-01: HTTPS/TLS 1.3 only, Cloud Armor WAF
- [ ] SEC-02: Split API keys stored as HMAC-SHA256 hash
- [ ] SEC-03: AES-256 encryption at rest, TLS 1.3 in transit
- [ ] SEC-04: Client data isolation (ClickHouse partitions)
- [ ] SEC-05: RBAC (Owner > Admin > Engineer > Analyst > Viewer)
- [ ] SEC-06: Health Check API keys in-memory only, never persisted

### Out of Scope

- **Uncertainty Engine** — needs logprob access + consistency-based estimation, ships in V2 (Week 9-10)
- **Context Engine** — NeMo Guardrails integration, Safety Engine covers 80% of attack surface, V2
- **Cognitive Engine** — TransformerLens, scientifically deep, needs months of production data, V3
- **Behavior Engine** — Mirror Room + Shadow Testing, needs 6 months of traffic data, V3
- **Focus Engine** — domain drift (4% weight), Grounding+Consistency deliver 10x more value, V2/V3
- **Control Mode** — auto-block/retry/reroute via proxy, requires gateway architecture, V2
- **Self-healing / Auto-retry** — needs Control Mode proxy infrastructure, V2
- **Multi-model judge** — V3 Enterprise feature
- **Model routing** — different product entirely, never
- **D3.js network graphs** — Behavior Engine visualization, V3
- **Kafka** — Cloud Pub/Sub is sufficient for V1 scale

## Context

- **Market:** AI trust/observability is an emerging category. Competitors (Arize, LangSmith, Helicone) focus on observability — ZROKY focuses on trust scoring + certification.
- **Tech decisions already made:** Next.js 14, Fastify, Python/FastAPI microservices, GCP/GKE, ClickHouse, PostgreSQL, Redis, BigQuery.
- **V1 ships 4 of 9 engines:** Safety (30%), Grounding (25%), Consistency (20%), System (10%), Coverage bonus (15%).
- **Upgraded capabilities:** LLM Safety Judge (Llama-3-8B), Ragas claim-level attribution, DeepEval hallucination metrics, Evidently AI drift detection, cost-per-outcome intelligence, Monitor + Assist modes.
- **Build timeline from V1 Scope:** Phase 1 (Weeks 1-8) = functional V1 product, Phase 2 (Weeks 9-16) = expansion + viral launch.
- **Launch strategy:** Simultaneous launch — OSS + Health Check + Badge + Framework listings all go live on the same day.

## Constraints

- **Tech Stack**: Next.js 14, Fastify, Python/FastAPI, GCP/GKE, ClickHouse, PostgreSQL 15, Redis, BigQuery — already decided
- **Timeline**: Phase 1 (Weeks 1-8) must produce a paying-customer-ready product
- **Team**: 4 engineers initially, +1 AI/ML engineer in Phase 2
- **Architecture**: Microservices — each engine = 1 Python/FastAPI worker
- **Performance**: Signup to live Trust Score in under 15 minutes
- **Security**: OWASP Top 10, TLS 1.3, AES-256, HMAC-SHA256 API keys, Cloud Armor WAF

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 4 engines in V1 (not 9) | 4 engines at 95% quality > 9 at 60% | — Pending |
| Safety gets 30% weight (not 20%) | #1 reason companies buy, recalibrated for 4-engine system | — Pending |
| Grounding + Consistency over Focus | Combined 45% weight vs Focus's 4%, 10x more user value | — Pending |
| LLM Safety Judge (Llama-3-8B) | Catches subtle attacks pattern-matching misses, self-hosted for cost | — Pending |
| Ragas + DeepEval for Grounding | Claim-level attribution + hallucination scoring, industry standard | — Pending |
| Evidently AI for Consistency | Explicit PSI/KL/Wasserstein/JS drift metrics, production-grade | — Pending |
| Cost-per-outcome in System Engine | Goes beyond raw cost to measure cost per successful outcome | — Pending |
| Monitor + Assist modes (Control = V2) | Enterprises need gradual adoption path, proxy not needed for V1 | — Pending |
| Cloud Pub/Sub (not Kafka) | Sufficient for V1 scale, managed service, lower ops overhead | — Pending |
| Simultaneous launch strategy | One big story > four small stories, all viral moves amplify each other | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-09 after initialization*
