# ROADMAP.md — ZROKY AI Trust Infrastructure V1

**Milestone:** v1.0 — Production-ready AI Trust Platform
**Generated:** 2026-04-09 | **Phases:** 12 | **Total Plans:** ~85 estimated

---

## Phase 1: Project Scaffold + CI/CD
- **Goal:** Enterprise-grade monorepo structure, linting, formatting, CI/CD pipeline — zero business logic
- **Requirements:** INFRA-07 (partial)
- **Success criteria:** `pnpm install` works, `pnpm lint` passes, `pnpm test` passes, GitHub Actions green
- **Estimated plans:** 6-8
- **Status:** Not started

## Phase 2: Infrastructure (Terraform + Databases)
- **Goal:** All GCP infrastructure provisioned via Terraform — GKE, Cloud SQL, ClickHouse, Redis, Pub/Sub
- **Requirements:** INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06
- **Success criteria:** `terraform apply` creates full environment, all services reachable from GKE
- **Depends on:** Phase 1
- **Estimated plans:** 8-10
- **Status:** Not started

## Phase 3: Database Schemas + Security Foundation
- **Goal:** PostgreSQL tables + RLS, ClickHouse tables + partitioning, Redis key structure, encryption verified
- **Requirements:** SEC-01, SEC-02, SEC-03, SEC-04, INFRA-02 (schema), INFRA-03 (schema)
- **Success criteria:** All tables created, RLS policies active, multi-tenant isolation test passes
- **Depends on:** Phase 2
- **Estimated plans:** 6-8
- **Status:** Not started

## Phase 4: API Server + Authentication
- **Goal:** Fastify server with Clerk auth, API key management, rate limiting, event ingestion, universal envelope
- **Requirements:** API-01, API-02, API-03, API-05, API-06, API-07, API-08, ONBOARD-02, ONBOARD-03, SEC-05
- **Success criteria:** Send event via API → lands in Pub/Sub, auth works, rate limited, OpenAPI docs served
- **Depends on:** Phase 3
- **Estimated plans:** 8-10
- **Status:** Not started

## Phase 5: Safety Engine
- **Goal:** Full Safety Engine — prompt injection, jailbreak, PII, toxicity, data extraction, campaigns, LLM Judge, escalation
- **Requirements:** SAFE-01, SAFE-02, SAFE-03, SAFE-04, SAFE-05, SAFE-06, SAFE-07, SAFE-08
- **Success criteria:** Safety events consumed from Pub/Sub, all 8 detectors work, LLM Judge callable, scores in ClickHouse
- **Depends on:** Phase 4 (events flowing through Pub/Sub)
- **Estimated plans:** 8-10
- **Status:** Not started

## Phase 6: Grounding Engine
- **Goal:** Full Grounding Engine — RAG quality, answer-source consistency, factual check, golden tests, Ragas, DeepEval
- **Requirements:** GRND-01, GRND-02, GRND-03, GRND-04, GRND-05, GRND-06, GRND-07
- **Success criteria:** Grounding events consumed, Ragas + DeepEval scores computed, results in ClickHouse
- **Depends on:** Phase 4
- **Estimated plans:** 7-8
- **Status:** Not started

## Phase 7: Consistency + System Engines
- **Goal:** Both engines — drift detection (Evidently), benchmarking, regression testing, latency/cost/uptime monitoring
- **Requirements:** CONS-01, CONS-02, CONS-03, CONS-04, CONS-05, SYS-01, SYS-02, SYS-03, SYS-04, SYS-05, SYS-06, SYS-07
- **Success criteria:** Both engines consume events, all metrics computed, stored in ClickHouse
- **Depends on:** Phase 4
- **Estimated plans:** 8-10
- **Status:** Not started

## Phase 8: Trust Score Computer
- **Goal:** Aggregation engine — weighted formula, override rules, cold-start handling, status bands
- **Requirements:** TRUST-01, TRUST-02, TRUST-03, TRUST-04
- **Success criteria:** All 4 engine scores → weighted Trust Score matches manual calculation, overrides trigger correctly
- **Depends on:** Phase 5, Phase 6, Phase 7 (all engines producing scores)
- **Estimated plans:** 5-6
- **Status:** Not started

## Phase 9: Dashboard
- **Goal:** Next.js dashboard — 3 views (SMB, Engineer, Executive), real-time WebSocket, 30-day trends, alert center
- **Requirements:** DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06
- **Success criteria:** Dashboard loads, shows correct Trust Score, updates in real-time, all 3 views working
- **Depends on:** Phase 8 (Trust Score available), Phase 4 (API)
- **Estimated plans:** 8-10
- **Status:** Not started

## Phase 10: SDK + Onboarding + Integrations
- **Goal:** Python + Node.js + Go SDKs, onboarding flow, LangChain/LangGraph/LiteLLM connectors
- **Requirements:** SDK-01, SDK-02, SDK-03, ONBOARD-01, INT-01, INT-02, INT-03, MODE-01, MODE-02
- **Success criteria:** `pip install zroky` + send event + see score in dashboard in < 15 minutes
- **Depends on:** Phase 9 (dashboard visible), Phase 4 (API)
- **Estimated plans:** 7-8
- **Status:** Not started

## Phase 11: Billing + Viral + Growth
- **Goal:** Stripe billing, tier enforcement, Health Check, Badge, OSS extraction, framework listings
- **Requirements:** BILL-01, BILL-02, API-06 (tier enforcement), OSS-01, HEALTH-01, BADGE-01, FRAME-01, ALERT-01, ALERT-02, API-04, API-09, SEC-06
- **Success criteria:** Billing works end-to-end, badge embeddable, health check returns results, OSS package installable
- **Depends on:** Phase 8 (Trust Score), Phase 10 (SDK)
- **Estimated plans:** 8-10
- **Status:** Not started

## Phase 12: Security Hardening + Launch Prep
- **Goal:** Penetration testing, E2E test suite, performance optimization, documentation site, launch execution
- **Requirements:** SEC-01 (audit), SEC-04 (audit), INFRA-07 (full CI/CD), all requirements validated
- **Success criteria:** Security audit clean, E2E tests pass, docs complete, performance targets met
- **Depends on:** All previous phases
- **Estimated plans:** 6-8
- **Status:** Not started

---

## Phase Dependency Graph

```
Phase 1 (Scaffold) ──► Phase 2 (Infra) ──► Phase 3 (Schemas) ──► Phase 4 (API)
                                                                       │
                                                    ┌──────────────────┼──────────────────┐
                                                    │                  │                  │
                                               Phase 5            Phase 6            Phase 7
                                              (Safety)          (Grounding)     (Consistency+Sys)
                                                    │                  │                  │
                                                    └──────────────────┼──────────────────┘
                                                                       │
                                                                  Phase 8
                                                               (Trust Score)
                                                                       │
                                                              ┌────────┴────────┐
                                                              │                 │
                                                         Phase 9           Phase 10
                                                        (Dashboard)       (SDK+Onboard)
                                                              │                 │
                                                              └────────┬────────┘
                                                                       │
                                                                  Phase 11
                                                              (Billing+Viral)
                                                                       │
                                                                  Phase 12
                                                                 (Launch)
```

**Parallelization opportunities:**
- Phase 5, 6, 7 can run in parallel (after Phase 4)
- Phase 9, 10 can run in parallel (after Phase 8)

---

## Coverage Matrix

Every requirement is assigned to exactly one phase:

| Phase | Requirements Covered |
|-------|---------------------|
| 1 | INFRA-07 (partial) |
| 2 | INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06 |
| 3 | SEC-01, SEC-02, SEC-03, SEC-04 |
| 4 | API-01, API-02, API-03, API-05, API-06, API-07, API-08, ONBOARD-02, ONBOARD-03, SEC-05 |
| 5 | SAFE-01 through SAFE-08 |
| 6 | GRND-01 through GRND-07 |
| 7 | CONS-01–05, SYS-01–07 |
| 8 | TRUST-01, TRUST-02, TRUST-03, TRUST-04 |
| 9 | DASH-01 through DASH-06 |
| 10 | SDK-01–03, ONBOARD-01, INT-01–03, MODE-01–02 |
| 11 | BILL-01–02, API-04, API-06 (enforcement), API-09, OSS-01, HEALTH-01, BADGE-01, FRAME-01, ALERT-01–02, SEC-06 |
| 12 | INFRA-07 (full), all requirements verified |

**Unassigned requirements:** 0 / 73

---
*Generated: 2026-04-09 | Milestone v1.0*
