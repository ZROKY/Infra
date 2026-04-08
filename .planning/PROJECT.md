# ZROKY — AI Trust Infrastructure Platform

## What This Is

ZROKY is a production-grade AI Trust Infrastructure platform that monitors, scores, and certifies the trustworthiness of AI agents in real-time. A developer signs up, installs the SDK (pip/npm), connects their AI agent, and sees a live Trust Score on their dashboard within 15 minutes. V1 ships with 4 engines (Safety, Grounding, Consistency, System), a free Health Check scanner, an embeddable AI Trust Badge, and an open-source SDK — all launching simultaneously on Day 1.

## Core Value

A developer can sign up, connect their AI in 15 minutes, see a live Trust Score, get alerts, embed a Trust Badge, and tell their team "we need the paid plan."

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Engines:**
- [ ] **ENG-01**: Safety Engine (30% weight) — prompt injection, jailbreak, PII, toxicity, data extraction, campaign detection, LLM Safety Judge (Llama-3-8B), attack progression detection
- [ ] **ENG-02**: Grounding Engine (25% weight) — RAG retrieval quality, answer-source consistency, factual consistency, golden test sets, vector DB health, claim-level attribution (Ragas), hallucination metrics (DeepEval)
- [ ] **ENG-03**: Consistency Engine (20% weight) — daily benchmarks, regression testing, behavioral drift (Evidently AI — PSI/KL/Wasserstein/JS), behavioral fingerprinting, provider version tracking
- [ ] **ENG-04**: System Engine (10% weight) — latency, errors, cost, uptime, throughput, cost-per-outcome intelligence, performance-quality correlation
- [ ] **ENG-05**: Coverage Intelligence (15% bonus) — ensures trust score is honest about data gaps

**Trust Score:**
- [ ] **TSC-01**: 4-engine weighted composite Trust Score computation
- [ ] **TSC-02**: Override rules (Safety < 40 → Trust Score capped at 50)
- [ ] **TSC-03**: Cold-start handling (< 10 events = no score, 10-99 = provisional)
- [ ] **TSC-04**: Trust Score status bands (Critical/Warning/Good/Excellent)

**Dashboard:**
- [ ] **DSH-01**: SMB Simplified View (Trust Score + 3 panels)
- [ ] **DSH-02**: Engineer View (4-engine detail + incidents)
- [ ] **DSH-03**: Executive View (multi-agent portfolio, Growth+ only)
- [ ] **DSH-04**: 30-day Trust Score trend chart (Recharts)
- [ ] **DSH-05**: Alert center (in-dashboard feed)

**API:**
- [ ] **API-01**: Event ingestion (POST /events — single + batch)
- [ ] **API-02**: Trust Score query (GET /trust-score/{agent_id})
- [ ] **API-03**: Management API (agents, rules, incidents CRUD)
- [ ] **API-04**: Webhooks outbound (push events to client endpoints)

**SDK:**
- [ ] **SDK-01**: Python SDK (pip install zroky)
- [ ] **SDK-02**: Node.js SDK (npm install @zroky/sdk)
- [ ] **SDK-03**: Go SDK stub (basic client only)

**Alerts:**
- [ ] **ALR-01**: Email alerts (SendGrid, all tiers)
- [ ] **ALR-02**: Slack alerts (webhook-based, Growth+ only)

**Integrations:**
- [ ] **INT-01**: LangChain ZROKYCallbackHandler
- [ ] **INT-02**: LangGraph ZROKYGraph wrapper
- [ ] **INT-03**: LiteLLM proxy mode telemetry reader

**Viral Systems:**
- [ ] **VIR-01**: OSS SDK + Safety Engine on GitHub (MIT + BSL)
- [ ] **VIR-02**: Free AI Health Check (zroky.ai/scan — Llama-3-8B judge, 50-prompt test suite)
- [ ] **VIR-03**: AI Trust Badge (badge.zroky.ai — embeddable widget, domain verification)
- [ ] **VIR-04**: Framework listings (LangChain, Vercel AI SDK PR submissions)

**Modes of Operation:**
- [ ] **MOD-01**: Monitor Mode — observe + score + alert (no intervention)
- [ ] **MOD-02**: Assist Mode — monitor + suggestions + draft actions

**Onboarding:**
- [ ] **ONB-01**: Signup to Trust Score in under 15 minutes
- [ ] **ONB-02**: Guided SDK setup wizard in dashboard

**Security:**
- [ ] **SEC-01**: Clerk auth (email/password + MFA + magic link)
- [ ] **SEC-02**: API key authentication (split ingest/read keys)
- [ ] **SEC-03**: Cloud Armor WAF + DDoS protection

**Billing:**
- [ ] **BIL-01**: Stripe integration (plans + trial + overage handling)
- [ ] **BIL-02**: 4 pricing tiers (Developer free, SMB $99, Growth $499, Enterprise custom)

**Infrastructure:**
- [ ] **INF-01**: GCP/GKE deployment (us-central1, auto-scaling)
- [ ] **INF-02**: PostgreSQL 15 (Cloud SQL) — operational data
- [ ] **INF-03**: ClickHouse (Altinity on GKE) — analytics (billions of rows)
- [ ] **INF-04**: Redis (Cloud Memorystore) — cache + rate limits
- [ ] **INF-05**: Cloud Pub/Sub — event queue (1 topic per engine)
- [ ] **INF-06**: Terraform IaC for all resources
- [ ] **INF-07**: CI/CD (Cloud Build + GitHub Actions)

### Out of Scope

- **Uncertainty Engine** — V2 (needs V1 data patterns first)
- **Context Engine** — V2 (requires conversation tracking infrastructure)
- **Cognitive Engine** — V3 (needs TransformerLens + GPU, enterprise only)
- **Behavior Engine** — V3 (needs multi-agent topology data)
- **Focus Engine** — V3 (needs purpose vector embeddings)
- **Control Mode (proxy/gateway)** — V2 (requires architectural shift, V1 is observe-only)
- **Resolution Intelligence (GPT-4o diagnosis)** — V2
- **Self-healing / Auto-retry** — V2
- **Multi-model judge** — V3 Enterprise
- **GraphQL API** — V4
- **SSO (Okta, Azure AD)** — V3 Enterprise
- **EU/APAC regions** — V3/V4
- **SOC 2 Type II certification** — V4
- **AutoGen, CrewAI, LlamaIndex integrations** — V2/V3

## Context

**Product Category:** AI Trust Infrastructure — new category, no direct competitor doing trust scoring of AI agents at scale.

**Market Timing:** Enterprise AI adoption exploding (2025-2026). Companies deploying AI agents but zero visibility into whether they're trustworthy. ZROKY fills this gap.

**Technical Architecture:** Microservices (1 service per engine) on GKE. Event-driven via Cloud Pub/Sub. Hot path: gateway → Pub/Sub → engine workers → ClickHouse → Trust Score aggregation. Dashboard: Next.js 14 with real-time WebSocket updates.

**V1 Technology Stack:**
- Frontend: Next.js 14 (App Router), Tailwind CSS + shadcn/ui, Recharts, Socket.io, Clerk, Stripe.js
- API Layer: Fastify (Node.js), Kong API Gateway
- Engine Workers: Python/FastAPI (each engine = 1 microservice)
- AI/ML: guardrails-ai, NeMo Guardrails, promptfoo, lm-evaluation-harness, Phoenix (Arize), Langfuse, Ragas, DeepEval, Evidently AI, Llama-3-8B (vLLM), LiteLLM, OpenLLMetry
- Databases: PostgreSQL 15, ClickHouse, Redis, BigQuery
- Infrastructure: GCP/GKE, Cloud Pub/Sub, Terraform, Cloud Build, Secret Manager, Cloud Armor

**Pricing:**
- Developer: Free (1 agent, 10K interactions/month)
- SMB: $99/month (1 agent, 500K interactions)
- Growth: $499/month (5 agents, 5M interactions)
- Enterprise: Custom ($2K-$15K+/month)

**Cost Targets:** $3,300-5,100/month at launch. Breakeven at ~50 SMB clients. Target Month 4: 100 clients, $15K+ MRR.

## Constraints

- **Timeline**: 16-week build (Weeks 1-8 Foundation, Weeks 9-16 Polish + Viral + Launch)
- **Team**: 4 engineers (1 infrastructure, 2 backend, 1 frontend)
- **Budget**: Infrastructure ~$3,500-5,000/month at launch
- **Performance**: TTFTS < 15min, API P95 < 10ms ingest / < 50ms query, Trust Score lag < 30s, Dashboard < 2s
- **Reliability**: 99.9% API uptime, 0% data loss, < 5% alert false positive rate
- **Security**: SOC 2 readiness (not certification), all PII redacted, API keys never logged
- **Scalability**: Architecture must handle 100→10,000 clients without rearchitecture

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 4 engines in V1 (not 9) | 4 engines at 95% quality > 9 engines at 60% quality | — Pending |
| Safety Engine gets 30% weight | Safety is #1 reason companies buy. Non-negotiable floor. | — Pending |
| Simultaneous launch (OSS + Health Check + Badge + Platform) | One massive story > four small announcements | — Pending |
| Observe-only in V1 (Monitor + Assist, no Control) | Control Mode needs proxy architecture, too risky for V1 | — Pending |
| GCP over AWS | Better Kubernetes experience, Cloud Pub/Sub > SQS for event-driven | — Pending |
| ClickHouse over TimescaleDB | Better at billions of analytical rows, column-oriented | — Pending |
| Fastify + Python hybrid | Fastify for API speed, Python for ML/AI engine libraries | — Pending |
| Ragas + DeepEval (both) | Ragas = claim-level WHERE, DeepEval = scoring HOW BAD | — Pending |
| Evidently AI for drift | Explicit PSI/KL/Wasserstein/JS metrics, not custom implementation | — Pending |
| Llama-3-8B as Safety Judge | Self-hosted, no vendor lock-in for safety-critical path, < 500ms | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-09 after initialization*
