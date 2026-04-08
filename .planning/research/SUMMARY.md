# Research Summary — ZROKY AI Trust Infrastructure

**Synthesized:** 2026-04-09 | **Research docs:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

## Key Findings

### 1. Tech Stack is Production-Ready
All V1 tech choices validated. One modification recommended:
- **Defer Kong API Gateway** → Use Fastify middleware for rate limiting in V1
- **All other choices confirmed**: Next.js 14, Fastify, Python/FastAPI, GCP/GKE, ClickHouse, PostgreSQL 15, Redis, BigQuery, Cloud Pub/Sub, Terraform

Anti-recommended alternatives avoided: Kafka, Express, MongoDB, Supabase, Vercel hosting, GraphQL, Prisma ORM.

### 2. Competitive Position is Strong
- **11 differentiators** vs competition (Arize, LangSmith, Helicone, Braintrust)
- **Unified Trust Score (0-100)** is the core IP — nobody else has a single number
- **All 10 table-stakes features** covered — no gaps
- **8 anti-features** clearly scoped out — no scope creep risk
- ZROKY is positioned as **trust infrastructure**, not another observability tool

### 3. Architecture is Clean but Complex
- 6 independently deployable services (API, 4 engines, Trust Score Computer)
- Fan-out event processing via Cloud Pub/Sub
- Dual database strategy: PostgreSQL (OLTP) + ClickHouse (OLAP)
- Real-time push via Redis + WebSocket
- Build order: Foundation → API → Engines → Dashboard → SDK → Billing → Launch

### 4. Top Risks Identified (Ordered by Priority)

| # | Risk | Why Critical | Prevention |
|---|------|-------------|------------|
| 1 | Multi-tenant data isolation | Security/legal liability. Must be right from Day 1. | RLS policies, client_id in every query, automated isolation tests |
| 2 | ClickHouse query performance | Dashboard becomes unusable as data grows | Proper partitioning + ORDER BY + materialized views from start |
| 3 | Pub/Sub message handling | Trust Scores computed from corrupted event streams | Idempotent processors, ReplacingMergeTree, time-window aggregation |
| 4 | Safety Engine false positives | Users abandon platform if flagged incorrectly | LLM Safety Judge for gray areas, per-client tuning, dispute mechanism |
| 5 | Trust Score gaming | Undermines platform's core value proposition | Coverage Score (15% weight), volume anomaly detection, badge transparency |

### 5. Critical Path for V1

```
Auth → API Keys → Event Ingestion → Engine Processing → Trust Score → Dashboard → SDK → Onboarding
```

Everything else (alerts, badge, health check, billing, OSS) branches off the critical path.

## Roadmap Recommendations

Based on research findings, recommended phase structure:

1. **Foundation** — Terraform, CI/CD, DB schemas, project scaffold
2. **API + Auth** — Fastify, Clerk, API keys, rate limiting
3. **Safety Engine** — Highest-priority engine (30% weight), most complex
4. **Grounding Engine** — Second priority (25% weight), Ragas integration
5. **Consistency + System Engines** — Simpler engines, can parallelize
6. **Trust Score Computer** — Aggregation, formula, override rules
7. **Dashboard** — Next.js, 3 views, WebSocket, real-time
8. **SDK + Onboarding** — Python, Node.js, Go stub, quick-start flow
9. **Alerts + Integration** — Email, Slack, webhooks, LangChain connectors
10. **Billing + Viral** — Stripe, badge, health check, OSS extraction
11. **Security + Testing** — Hardening, E2E tests, penetration testing
12. **Launch** — Documentation, landing page, beta program

## Confidence Assessment

| Area | Confidence | Notes |
|------|-----------|-------|
| Tech stack choices | 95% | All validated, well-documented alternatives |
| Architecture design | 90% | Clean separation, but V1→V2 scaling needs attention |
| Feature scope | 95% | Very clear what's in/out |
| Risk identification | 85% | 10 pitfalls documented, may be unknown unknowns in LLM integration |
| Build order | 90% | Critical path is clear, parallelization opportunities identified |
| Timeline feasibility | 70% | Fine granularity (12 phases) is ambitious — depends on team velocity |

---
*Generated: 2026-04-09*
