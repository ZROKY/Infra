# Features Research — ZROKY AI Trust Infrastructure

**Researched:** 2026-04-09 | **Source:** V1 Scope Document + Market Analysis

## Table Stakes (Must Have or Users Leave)

These are features users expect from ANY AI monitoring/trust platform:

| Feature | ZROKY V1 Status | Complexity | Notes |
|---------|-----------------|------------|-------|
| Real-time monitoring dashboard | ✅ In scope | HIGH | 3 views (SMB, Engineer, Executive) |
| API key-based authentication | ✅ In scope | LOW | Split keys (ingest/manage/agent) |
| SDK (Python + JS minimum) | ✅ In scope | MEDIUM | Python + Node.js + Go stub |
| Event ingestion API | ✅ In scope | MEDIUM | Single + batch endpoints |
| Alert system (email minimum) | ✅ In scope | LOW | Email (SendGrid) + Slack |
| Data visualization / charts | ✅ In scope | MEDIUM | Recharts 30-day trends |
| Team/org management | ✅ In scope | LOW | Clerk RBAC |
| Billing / subscription | ✅ In scope | MEDIUM | Stripe, 4 tiers |
| Documentation site | ✅ In scope | LOW | Mintlify docs.zroky.ai |
| HTTPS + basic security | ✅ In scope | LOW | TLS 1.3 + Cloud Armor |

**Assessment:** All table stakes covered. No gaps.

## Differentiators (Competitive Advantage)

What makes ZROKY different from Arize, LangSmith, Helicone, Braintrust:

| Feature | Category | ZROKY V1 | Competition has it? |
|---------|----------|----------|-------------------|
| **Unified Trust Score (0-100)** | Core IP | ✅ | ❌ Nobody has a single trust number |
| **Multi-engine architecture** | Core IP | ✅ (4 engines) | ❌ Others monitor individual metrics |
| **Override rules** | Core IP | ✅ | ❌ No safety-floor concept elsewhere |
| **AI Trust Badge** | Viral | ✅ | ❌ Unique to ZROKY |
| **Free Health Check** | Viral | ✅ | ❌ Nobody offers free AI scan |
| **OSS Safety Engine** | Viral | ✅ | Partial (guardrails-ai is OSS but not trust-scored) |
| **Claim-level hallucination** | Technical | ✅ (Ragas) | Partial (Ragas exists but not integrated into trust score) |
| **Cost-per-outcome** | Technical | ✅ | ❌ Others track cost per request, not per success |
| **Behavioral drift detection** | Technical | ✅ (Evidently) | ❌ Nobody combines drift + trust scoring |
| **LLM Safety Judge** | Technical | ✅ (Llama-3-8B) | ❌ Self-hosted judge for safety is unique |
| **Monitor + Assist modes** | UX | ✅ | Partial (some offer actions but not scored modes) |

**Assessment:** 11 differentiators. Strong competitive moat even in V1.

## Anti-Features (Deliberately NOT Building)

| Feature | Why NOT | When (if ever) |
|---------|---------|-----------------|
| Control Mode (proxy/gateway) | Adds massive infra complexity. V1 = observe don't intervene. | V2 |
| Model routing / optimization | Different product. ZROKY monitors trust, not optimizes cost. | Never |
| Prompt engineering tools | Not our market. LangSmith, PromptLayer own this. | Never |
| Fine-tuning management | Not trust infrastructure. Different value prop entirely. | Never |
| Data labeling / annotation | Tooling market, not trust market. | Never |
| Custom model hosting | We judge models, we don't host them (except Safety Judge). | Never |
| Chat interface / playground | LangSmith, Vercel AI Playground own this. | Never |
| Dataset management | DeepEval, Ragas handle this in their tools. We consume results. | Never |

## Feature Dependencies

```
Authentication (Clerk) → API Keys → SDK → Event Ingestion → Engine Processing → Trust Score → Dashboard
                                                                                           → Alerts
                                                                                           → Badge
                                                                                           → Health Check

Billing (Stripe) → Tier enforcement → Rate limiting → API access

OSS Extraction ← Safety Engine validators ← guardrails-ai integration
```

**Critical path:** Auth → API → SDK → Ingestion → Engines → Trust Score → Dashboard → Onboarding flow

## Competitive Landscape Quick Map

| Competitor | Focus | Trust Score? | Pricing | Weakness |
|-----------|-------|-------------|---------|----------|
| Arize AI | ML observability | ❌ | Usage-based | No trust scoring, no safety focus |
| LangSmith | LLM development | ❌ | Per-trace | Dev tool not production monitoring |
| Helicone | LLM gateway | ❌ | Free + usage | Proxy-only, shallow analysis |
| Braintrust | LLM evaluation | ❌ | Per-eval | Eval-focused, not runtime monitoring |
| Galileo | LLM reliability | Partial | Enterprise | No public trust score, no badge |
| **ZROKY** | **AI Trust** | **✅ (0-100)** | **Tiered (free-enterprise)** | **New entrant, no brand** |

**ZROKY's positioning:** Not another observability tool. Trust infrastructure = monitoring + scoring + certification + public proof.

---
*Generated: 2026-04-09*
