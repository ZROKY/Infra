# Stack Research — ZROKY AI Trust Infrastructure

**Researched:** 2026-04-09 | **Source:** V1 Scope Document (2,513 lines)

## Frontend

### Next.js 14 (App Router) — ✅ VALIDATED
- **Version:** 14.2.x
- **Rationale:** Server Components reduce client bundle, App Router streaming for real-time dashboard. Dominant SaaS dashboard choice.
- **Confidence:** HIGH
- **Note:** Next 15 available but 14 is more battle-tested. Clean migration path later.

### Tailwind CSS + shadcn/ui — ✅ VALIDATED
- **Version:** Tailwind 3.4.x, shadcn/ui latest
- **Rationale:** Copy-paste components (not npm dep), fully customizable, dark mode built-in. Perfect for dashboard-heavy product.
- **Confidence:** HIGH

### Recharts — ✅ VALIDATED
- **Version:** 2.12.x
- **Rationale:** React-native, lightweight, handles time-series (Trust Score 30-day trends).
- **Confidence:** MEDIUM — consider Tremor for V2 if charts get complex.

### Socket.io — ✅ VALIDATED
- **Version:** 4.7.x
- **Rationale:** Battle-tested WebSocket with fallback. Real-time Trust Score updates.
- **Confidence:** HIGH

### Clerk — ✅ VALIDATED
- **Rationale:** Drop-in auth (MFA, magic links, RBAC, sessions). Saves 2-3 weeks. First-class Next.js integration.
- **Confidence:** HIGH

### Stripe — ✅ VALIDATED
- **Rationale:** Industry standard SaaS billing. Subscriptions, trials, metered billing (event overages).
- **Confidence:** HIGH — no alternatives needed.

## Backend — API Layer

### Fastify (Node.js) — ✅ VALIDATED
- **Version:** 4.28.x
- **Rationale:** 2-3x faster than Express. Schema validation built-in. Plugin architecture matches modular API design.
- **Confidence:** HIGH

### Kong API Gateway — ⚠️ REVISIT
- **Version:** 3.7.x OSS
- **Rationale:** Rate limiting, API key auth, routing, analytics.
- **Confidence:** MEDIUM
- **Recommendation:** For V1, start with Fastify middleware for rate limiting + key validation. Add Kong in V2 when multi-region matters. Reduces initial complexity.

## Backend — Engine Workers

### Python / FastAPI — ✅ VALIDATED
- **Version:** Python 3.12+, FastAPI 0.111.x
- **Rationale:** All AI/ML libs are Python-first. guardrails-ai, Ragas, DeepEval, Evidently — all native Python. Non-negotiable.
- **Confidence:** HIGH

### guardrails-ai — ✅ VALIDATED (v0.5.x)
Pre-built validators for PII, toxicity, prompt injection. Pluggable architecture. HIGH confidence.

### NVIDIA NeMo Guardrails — ⚠️ VALIDATED WITH CAUTION (v0.10.x)
5-rail system for defense-in-depth. MEDIUM confidence — can be heavy. Consider lazy-loading.

### promptfoo — ✅ VALIDATED (v0.90.x+)
Red team signatures (100+ attack patterns) + regression testing. HIGH confidence.

### lm-evaluation-harness — ✅ VALIDATED (v0.4.x)
Standard benchmark suite for Consistency Engine daily benchmarks. HIGH confidence.

### Phoenix (Arize) — ✅ VALIDATED (v4.x+)
OpenInference RAG evaluation. Trace-level observability. Open-source. HIGH confidence.

### Langfuse — ✅ VALIDATED (v2.x)
LLM-as-judge pipeline. Self-hostable for data sovereignty. HIGH confidence.

### Ragas — ✅ VALIDATED (v0.2.x)
Claim-level attribution (faithfulness, relevancy, precision, recall). Industry standard. HIGH confidence.

### DeepEval — ✅ VALIDATED (v1.x)
Hallucination scoring beyond Ragas. G-Eval, contextual relevancy. Complements Ragas. HIGH confidence.

### Evidently AI — ✅ VALIDATED (v0.4.x)
Production drift detection (PSI, KL, Wasserstein, JS). HTML reports. CI/CD test suites. HIGH confidence.

### LiteLLM — ✅ VALIDATED (v1.x)
Unified API across 100+ LLM providers. Proxy mode captures model metrics. HIGH confidence.

### OpenLLMetry — ✅ VALIDATED (v0.28.x)
OpenTelemetry for LLMs. Standard-based, vendor-neutral. HIGH confidence.

### Llama-3-8B via vLLM — ✅ VALIDATED
Llama 3.1 8B, vLLM 0.6.x on Cloud Run with GPU. LLM Safety Judge: <500ms, ~$0.001/call. HIGH confidence.

## Databases

### PostgreSQL 15 (Cloud SQL) — ✅ VALIDATED
Operational data. ACID, robust RBAC, proven at scale. HIGH confidence.

### ClickHouse (Altinity on GKE) — ✅ VALIDATED (v24.x)
Columnar OLAP for billions of trust_events. 100x faster than PG for analytics. HIGH confidence.

### Redis (Cloud Memorystore) — ✅ VALIDATED (v7.x)
Trust Score cache (sub-ms), rate limiting (atomic ops), sessions. HIGH confidence.

### BigQuery — ✅ VALIDATED
Long-term aggregation, cross-client analytics. Serverless, pay-per-query. HIGH confidence.

## Infrastructure

### GCP / GKE — ✅ VALIDATED
Auto-scaling engine workers. Cloud SQL, Memorystore, Pub/Sub, BigQuery as managed services. HIGH confidence.

### Cloud Pub/Sub — ✅ VALIDATED
Event queue (1 topic per engine). Managed, auto-scaling. No ops overhead. HIGH confidence.

### Terraform — ✅ VALIDATED (v1.9.x)
IaC standard. GCP provider is first-class. HIGH confidence.

### Cloud Build + GitHub Actions — ✅ VALIDATED
GH Actions for CI (tests, lint), Cloud Build for CD (deploy to GKE). HIGH confidence.

## Anti-Recommendations

| Tool | Why NOT |
|------|---------|
| Kafka | Overkill for V1. Pub/Sub handles 10M+ msg/day. Revisit at 100M/day. |
| Express.js | 2-3x slower than Fastify. No schema validation. |
| MongoDB | Wrong for analytics. ClickHouse is 100x faster for OLAP. |
| Supabase | Ties to their ecosystem. Need independent PG + ClickHouse. |
| Vercel hosting | Can't run Python workers, ClickHouse, or Kubernetes. Marketing site only. |
| GraphQL | REST is simpler for CRUD + event ingestion. Adds complexity without benefit. |
| Prisma ORM | Adds abstraction over raw SQL that hurts ClickHouse queries. Use raw SQL. |

## Key Insight
The V1 stack is well-chosen. Only recommendation: defer Kong to V2, use Fastify middleware for rate limiting initially. Everything else is validated.

---
*Generated: 2026-04-09*
