# ZROKY V1 — COMPLETE SCOPE DOCUMENT
## Everything That Ships in Version 1.0
### End-to-End — From Architecture to Launch Day

> **Document Type:** V1 Scope Definition — The Shippable Product
> **Version:** 1.0 | **Date:** April 8, 2026
> **Relationship to Master Blueprint:** This document extracts the V1-specific subset from the 5,654-line Master Blueprint. The Blueprint is the *full vision*. This document is *what we build first*.
> **Success Criteria:** A developer can sign up, connect their AI in 15 minutes, see a live Trust Score, get alerts, embed a Trust Badge, and tell their team "we need the paid plan."

---

## TABLE OF CONTENTS

1. [V1 Product Definition — What Ships](#1-product)
2. [The 4 V1 Engines — Which 4 and Why](#2-engines)
3. [Trust Score V1 — Computation with 4 Engines](#3-trust-score)
4. [Technology Stack — V1 Only](#4-tech-stack)
5. [Database Schema — V1 Tables Only](#5-database)
6. [GCP Infrastructure — V1 Deployment](#6-infra)
7. [API — V1 Endpoints Only](#7-api)
8. [Dashboard — V1 Views Only](#8-dashboard)
9. [Onboarding Flow — Signup to Trust Score in 15 min](#9-onboarding)
10. [SDK — V1 Client Libraries](#10-sdk)
11. [Alerts — V1 Notification System](#11-alerts)
12. [Open-Source Strategy — What Ships Open on Day 1](#12-oss)
13. [Free AI Health Check — zroky.ai/scan](#13-health-check)
14. [AI Trust Badge — badge.zroky.ai](#14-badge)
15. [Framework Integrations — V1 Connectors](#15-frameworks)
16. [Security — V1 Requirements](#16-security)
17. [Pricing — V1 Tiers](#17-pricing)
18. [Build Roadmap — Week by Week](#18-roadmap)
19. [Simultaneous Launch Day Plan](#19-launch)
20. [V1 Success Metrics](#20-metrics)
21. [What Is NOT in V1 — Explicit Exclusions](#21-not-v1)

---

## 1. V1 PRODUCT DEFINITION — WHAT SHIPS

### 1.1 The V1 Promise

```
ZROKY V1 ships a WORKING AI Trust Infrastructure Platform:

  A developer signs up               → 2 minutes
  Installs SDK (pip/npm)             → 2 minutes
  Connects their AI agent            → 5 minutes
  Sees live Trust Score on dashboard → within 6 minutes of first event
  Gets Slack/email alert on issue    → immediately
  Embeds trust badge on website      → 2 minutes
  TOTAL: Signup to monitored AI      → under 15 minutes

V1 IS NOT: a demo, a prototype, or an MVP with asterisks.
V1 IS: a production-grade product that companies pay for.
```

### 1.2 V1 Feature Map — What's In

```
CATEGORY              V1 FEATURE                                STATUS
────────────────────  ─────────────────────────────────────────  ──────
ENGINES:
  Safety Engine       Prompt injection, jailbreak, PII, toxicity  ✅ V1
  Grounding Engine    RAG accuracy, source verification            ✅ V1
  Consistency Engine  Behavioral drift, regression detection       ✅ V1
  System Engine       Latency, errors, cost, uptime monitoring     ✅ V1

TRUST SCORE:
  4-engine scoring    Weighted composite (recalibrated for 4)      ✅ V1
  Override Rules      Critical safety = instant override           ✅ V1
  Cold-start handling < 10 events = no score, 10-99 = provisional  ✅ V1

DASHBOARD:
  SMB Simplified View Trust Score + 3 panels                      ✅ V1
  Engineer View       4-engine detail + incidents                  ✅ V1
  Executive View      Multi-agent portfolio (Growth+ only)         ✅ V1
  Trust Score chart   30-day trend line (Recharts)                 ✅ V1
  Alert Center        In-dashboard alert feed                     ✅ V1

API:
  Event Ingestion     POST /events (single + batch)               ✅ V1
  Trust Score Query   GET /trust-score/{agent_id}                 ✅ V1
  Management API      Agents, rules, incidents CRUD               ✅ V1
  Webhooks outbound   Push events to client endpoints             ✅ V1

SDK:
  Python SDK          pip install zroky                            ✅ V1
  Node.js SDK         npm install @zroky/sdk                      ✅ V1
  Go SDK              Stub release (basic client only)             ✅ V1

ALERTS:
  Email alerts        SendGrid, all tiers                         ✅ V1
  Slack alerts        Webhook-based, Growth+ only                 ✅ V1

INTEGRATIONS:
  LangChain           ZROKYCallbackHandler                        ✅ V1
  LangGraph           ZROKYGraph wrapper                          ✅ V1
  LiteLLM             Proxy mode telemetry reader                 ✅ V1

MODES OF OPERATION:
  Monitor Mode       Observe + score + alert (no intervention)    ✅ V1
  Assist Mode        Monitor + suggestions + draft actions        ✅ V1
  Control Mode       Auto-block/retry/reroute (proxy required)    ❌ V2

VIRAL:
  OSS SDK + Safety    GitHub public repo (MIT + BSL)              ✅ V1
  Health Check        zroky.ai/scan (free, no signup)             ✅ V1
  AI Trust Badge      badge.zroky.ai (embeddable widget)          ✅ V1
  Framework listings  LangChain, Vercel AI SDK submissions        ✅ V1

BILLING:
  Stripe integration  Plans + trial + overage handling            ✅ V1
  4 pricing tiers     Developer (free) → Enterprise               ✅ V1

AUTH:
  Clerk integration   Email/password + MFA + magic link           ✅ V1
```

### 1.3 Why These 4 Engines (My POV)

```
THE DECISION: 4 ENGINES, NOT 9.

9 engines on Day 1 = 9 engines at 60% quality.
4 engines on Day 1 = 4 engines at 95% quality.

WHICH 4 AND WHY:

1. SAFETY ENGINE (20% weight → recalibrated to 30% in V1)
   WHY FIRST: This is the #1 reason companies buy.
   "Is my AI being attacked? Is it leaking data? Is it safe?"
   If ZROKY can't answer this on Day 1, nothing else matters.
   Also: Safety Engine gets open-sourced (Move #3). 
   It's the hook. The first thing developers touch.
   
2. GROUNDING ENGINE (15% weight → recalibrated to 25% in V1)
   WHY SECOND: RAG systems are 70%+ of enterprise AI deployments.
   "Is my AI making stuff up or answering from real data?"
   This is the #2 pain point after safety.
   Grounding failures = direct customer damage (wrong medical info, 
   wrong financial advice, wrong product specs).
   
3. CONSISTENCY ENGINE (12% weight → recalibrated to 20% in V1)
   WHY THIRD: Silent model drift is the invisible killer.
   GPT-4o gets silently updated. Claude's behavior shifts.
   Companies don't notice until customers complain.
   Consistency catches what humans miss — slow degradation.
   Also: regression testing (promptfoo) is a clear developer value prop.
   
4. SYSTEM ENGINE (6% weight → recalibrated to 10% in V1)
   WHY FOURTH: Infrastructure basics. Latency, errors, uptime.
   Without System Engine, we can't tell if a Trust Score drop is because 
   the AI is misbehaving or because the server is on fire.
   Also: cheapest engine to build (LiteLLM + OpenLLMetry telemetry).
   Ships in Week 5, low risk.

WHAT'S EXPLICITLY OUT OF V1:

  ❌ Uncertainty Engine (15%) → V2 (Phase 2, Week 9-10)
     Needs logprob access for open models + consistency-based estimation for closed.
     Complex to calibrate. Not critical for first paying customers.
     
  ❌ Context Engine (10%) → V2 (Phase 2, Week 9-10)
     NeMo Guardrails integration. Valuable but Safety Engine covers 80% of 
     the attack surface Context Engine would catch. Ship it in Phase 2 
     when Safety Engine abuse patterns inform Context Engine design.
     
  ❌ Cognitive Engine (13%) → V3 (Phase 3, Weeks 17-20)
     TransformerLens integration for open models, proxy inference for closed.
     Scientifically deep. Requires calibration data from months of production traffic.
     
  ❌ Behavior Engine (5%) → V3 (Phase 3, Weeks 17-20)
     Mirror Room + Shadow Testing + Behavioral Fingerprinting.
     This is the moat. But moats need data. Ship after 6 months of traffic.
     
  ❌ Focus Engine (4%) → V1 Foundation ✅ (Week 5-6) 
     Wait — Focus Engine IS in V1 Foundation? 
     DECISION: NO. Swap it out.
     
     ORIGINAL Blueprint Phase 1 had: Safety + System + Focus.
     MY V1 RECOMMENDATION: Safety + Grounding + Consistency + System.
     
     WHY SWAP FOCUS FOR GROUNDING + CONSISTENCY:
     - Focus Engine (domain drift) is a nice-to-have. Score weight: 4%.
     - Grounding Engine answers "is my AI lying?" — weight: 15%.
     - Consistency Engine answers "is my AI changing?" — weight: 12%.
     - Combined value: Grounding + Consistency deliver 10× more user value
       than Focus for the same engineering effort.
     - Focus Engine can ship in V2 or V3 with minimal effort (cosine similarity
       against purpose vector — 1 week of work).

FINAL V1 ENGINE LINEUP:
  ┌───────────────────────────────────────────────────────┐
  │  ENGINE          │  V1 WEIGHT  │  V9 WEIGHT (later)  │
  ├───────────────────────────────────────────────────────┤
  │  Safety          │  30%        │  20%                 │
  │  Grounding       │  25%        │  15%                 │
  │  Consistency     │  20%        │  12%                 │
  │  System          │  10%        │   6%                 │
  │  Coverage bonus  │  15%        │  (replaced by more   │
  │                  │             │   engines later)     │
  ├───────────────────────────────────────────────────────┤
  │  TOTAL           │  100%       │                      │
  └───────────────────────────────────────────────────────┘

  Coverage bonus (15%): Rewards clients who send ALL their AI traffic,
  not just cherry-picked "good" interactions. This becomes Coverage 
  Intelligence (Section 2.4 of Master Blueprint) in the full 9-engine system.
  For V1, it's a simple ratio: events_received / expected_events.
```

---

## 2. THE 4 V1 ENGINES — DETAILED SPECIFICATION

### 2.1 ENGINE 1: SAFETY ENGINE (V1 Weight: 30%)

**What it does:** The AI's immune system. Protects against every known attack.

```
CAPABILITIES IN V1:

1. PROMPT INJECTION DETECTION
   ├── Pattern matching against 40+ known injection signatures
   ├── ML classifier (fine-tuned distilbert or similar lightweight model)
   ├── Cross-request correlation (same user trying variations)
   └── Source: promptfoo red-team signature library

2. JAILBREAK DETECTION
   ├── Known jailbreak signature matching (DAN, system prompt override, roleplay)
   ├── Encoding trick detection (base64-encoded instructions, unicode abuse)
   └── Score: 0-100 per attempt (blocked if > 80)

3. PII SCANNING + REDACTION
   ├── Powered by: guardrails-ai PII validator
   ├── Detects: names, emails, phone numbers, SSNs, credit cards, addresses
   ├── Action: redacts before storage (pseudonymization, not hashing)
   │   "John Smith at john@acme.com" → "<PERSON_REDACTED> at <EMAIL_REDACTED>"
   └── Config: client can toggle PII redaction on/off per agent

4. TOXICITY DETECTION
   ├── Powered by: guardrails-ai toxicity validator
   ├── Detects: hate speech, profanity, threats, sexual content
   └── Severity levels: low (log), medium (flag), high (block + alert)

5. DATA EXTRACTION DETECTION
   ├── Detects attempts to extract system prompts, API keys, internal configs
   ├── Pattern: "print your system message", "what's your instruction?"
   └── Uses promptfoo data extraction signatures

6. CAMPAIGN DETECTION
   ├── If 50+ similar attack patterns from different users/IPs in 1 hour
   ├── Raises CAMPAIGN alert (coordinated attack in progress)
   └── Escalates to critical severity automatically

7. LLM SAFETY JUDGE (V1 UPGRADE)
   ├── Powered by: Llama-3-8B (self-hosted on Cloud Run via vLLM)
   ├── Purpose: Catches subtle/novel attacks that pattern-matching misses
   ├── How it works:
   │   ├── Every flagged input (score 40-80) gets second-pass LLM judge review
   │   ├── Judge prompt: "Is this input attempting to manipulate, extract, or bypass safety?"
   │   ├── Returns: {verdict: safe|suspicious|malicious, confidence: 0-1, reasoning: string}
   │   └── If judge disagrees with pattern matcher → escalate for human review
   ├── Latency budget: < 500ms (Llama-3-8B is fast enough for real-time)
   ├── Cost: ~$0.001 per judge call (self-hosted, only called on flagged inputs)
   └── Why not GPT-4 as judge: Cost + latency + no vendor lock-in for safety-critical path

8. ATTACK PROGRESSION DETECTION (V1 UPGRADE)
   ├── Tracks per-user attack sophistication over time
   ├── Detects: user starts with simple prompts → escalates to encoded/multi-turn attacks
   ├── Progression stages: Probing → Testing → Exploiting → Exfiltrating
   ├── Each stage triggers escalating response (log → flag → throttle → block)
   └── Dashboard shows: attack progression timeline per suspicious user

TECHNOLOGY STACK:
  ├── guardrails-ai validators (PII, toxicity, prompt injection)
  ├── NVIDIA NeMo Guardrails (5-rail system: input → dialog → retrieval → execution → output)
  ├── promptfoo signature library (red team attack patterns)
  ├── Custom ML classifier for novel attack detection (trained on public datasets)
  ├── Llama-3-8B via vLLM (Cloud Run) — LLM Safety Judge for subtle attack detection
  └── Attack progression state machine (Redis-backed per-user tracking)

OVERRIDE RULE (from Master Blueprint):
  "If Safety Engine score < 40, Trust Score CANNOT exceed 50, regardless of other engines."
  This is hardcoded. A perfectly consistent, accurate AI that gets jailbroken is NOT trusted.
```

**Dashboard Output:**
```
SAFETY ENGINE — LIVE VIEW
─────────────────────────────────────────────────────
Safety Score:               91.2 / 100
Attack Attempts (24h):      47 | Blocked: 45 | Escalated: 2
Active Threats:             1 (systematic probe detected)
Top Attack Type:            DAN-style roleplay (34%)
Suspicious User:            user_id_8842 → 12 attempts, ban?
Campaign Alert:             NONE active

BREAKDOWN:
  Prompt Injection:  94/100  (14 attempts, 13 blocked)
  Jailbreak:         88/100  (8 attempts, 7 blocked)
  PII Exposure:      96/100  (3 near-misses redacted)
  Toxicity:          92/100  (12 flagged, 0 critical)
  Data Extraction:   89/100  (10 attempts, all blocked)
  LLM Judge Reviews: 23 today | 4 escalated to human review
  Attack Progression:user_8842 at Stage 3 (Exploiting) — auto-throttled
─────────────────────────────────────────────────────
```

---

### 2.2 ENGINE 2: GROUNDING ENGINE (V1 Weight: 25%)

**What it does:** Checks if the AI's answers are actually grounded in real facts.

```
CAPABILITIES IN V1:

1. RAG RETRIEVAL QUALITY MONITORING
   ├── Powered by: Phoenix (Arize) OpenInference evaluation
   ├── Measures: retrieval relevance score per query
   ├── Tracks: distance scores from vector DB (Pinecone/Qdrant/Weaviate)
   ├── Alerts when: retrieval quality drops below threshold (configurable)
   └── Why: 70%+ of enterprise AI uses RAG. Bad retrieval = bad answers.

2. ANSWER-SOURCE CONSISTENCY
   ├── Compares AI answer against the retrieved source documents
   ├── Uses LLM-as-judge via Langfuse (evaluator pipeline)
   ├── Score: how faithfully does the answer reflect the source?
   ├── Detects: AI making up information not in the source (hallucination)
   └── Example: Source says "price is $99" → AI says "$79" → Grounding failure

3. FACTUAL CONSISTENCY CHECK
   ├── For non-RAG systems: does the AI contradict itself across responses?
   ├── For RAG systems: does the answered content match the database?
   └── Uses embedding similarity between answer and golden test responses

4. GOLDEN TEST SET EVALUATION
   ├── Client uploads known Q&A pairs (golden dataset)
   ├── ZROKY runs these daily against the AI, tracks score trends
   ├── If score drops: model degradation or knowledge base drift
   └── Results shown on dashboard as trend chart

5. VECTOR DB HEALTH MONITORING
   ├── Tracks average distance score per query over time
   ├── Sudden increase in distance = embeddings are stale or corrupted
   ├── Alert: "Embedding quality degraded 15% — consider re-indexing"
   └── Supports: Pinecone, Qdrant, Weaviate, Chroma

6. CLAIM-LEVEL ATTRIBUTION (V1 UPGRADE — powered by Ragas)
   ├── Powered by: Ragas framework (ragas.io)
   ├── How it works:
   │   ├── Decomposes AI response into individual claims/statements
   │   ├── Each claim is traced back to specific source chunk(s)
   │   ├── Claims without source attribution = unsupported (potential hallucination)
   │   └── Score: supported_claims / total_claims = attribution_score
   ├── Metrics exposed:
   │   ├── Faithfulness — does each claim have source evidence?
   │   ├── Answer Relevancy — does the answer actually address the question?
   │   ├── Context Precision — are retrieved chunks actually useful?
   │   └── Context Recall — did retrieval find everything needed?
   ├── Why Ragas: Industry standard for RAG evaluation, integrates with LangChain natively
   └── Example:
       Response: "The price is $99 and ships in 2 days."
       → Claim 1: "price is $99" — SUPPORTED (source doc section 3.1)
       → Claim 2: "ships in 2 days" — UNSUPPORTED (source says 3-5 days)
       → Attribution Score: 50% ⚠️

7. HALLUCINATION METRICS (V1 UPGRADE — powered by DeepEval)
   ├── Powered by: DeepEval framework (deepeval)
   ├── Metrics beyond Ragas:
   │   ├── Hallucination Score — % of response that is fabricated
   │   ├── Contextual Relevancy — is the response relevant to retrieved context?
   │   ├── Answer Correctness — combining semantic + factual similarity
   │   └── G-Eval — LLM-based evaluation with custom criteria
   ├── Why BOTH Ragas + DeepEval:
   │   ├── Ragas = claim-level granularity (WHERE is the hallucination?)
   │   ├── DeepEval = comprehensive scoring (HOW BAD is the hallucination?)
   │   └── Together = complete hallucination detection pipeline
   └── Dashboard shows: per-claim breakdown + overall hallucination percentage

TECHNOLOGY STACK:
  ├── Phoenix (Arize) — OpenInference RAG evaluation
  ├── Langfuse — LLM-as-judge pipeline (configurable evaluators)
  ├── Ragas — claim-level attribution + RAG quality metrics (faithfulness, relevancy, precision, recall)
  ├── DeepEval — hallucination scoring + contextual relevancy + G-Eval
  ├── text-embedding-3-large — for embedding comparisons
  └── Custom Pinecone/Qdrant distance score tracker

OVERRIDE RULE:
  "If Grounding Engine detects > 10% hallucination rate in a 1-hour window,
   Trust Score drops by minimum 20 points."
```

**Dashboard Output:**
```
GROUNDING ENGINE — LIVE VIEW
─────────────────────────────────────────────────────
Grounding Score:            79.3 / 100  ⚠️
Retrieval Relevance:        84.1% (↓ 8.2% this week)
Answer Accuracy vs Source:  77.6%
Hallucination Rate:         4.8% (threshold: 3%)
Golden Test Score:          81/100 (was 88/100 last week)
Vector DB Health:           GOOD (avg distance: 0.23)

CLAIM-LEVEL ATTRIBUTION (Ragas):
  Total Claims Analyzed:    1,247 today
  Attribution Score:        82.3% (↑ from 78.1% last week)
  Unsupported Claims:       221 (17.7%) — top 5 shown below
  Context Precision:        86.4%  |  Context Recall: 79.8%

HALLUCINATION METRICS (DeepEval):
  Hallucination Score:      4.8%  ⚠️ (threshold: 3%)
  Contextual Relevancy:     88.2%
  Answer Correctness:       81.7%

TOP ISSUES:
  1. Product pricing data outdated in vector DB 
     → Action: Refresh product pricing embeddings
  2. AI citing wrong product model in 3% of cases
     → Action: Check document chunking quality
  3. 221 unsupported claims in shipping-related responses
     → Action: Update shipping FAQ in knowledge base
─────────────────────────────────────────────────────
```

---

### 2.3 ENGINE 3: CONSISTENCY ENGINE (V1 Weight: 20%)

**What it does:** Ensures the AI behaves the same way over time and across similar questions.

```
CAPABILITIES IN V1:

1. DAILY BENCHMARK TESTING
   ├── Powered by: lm-evaluation-harness
   ├── Runs standard test suite daily (configured per agent)
   ├── Tracks scores over time: 7-day, 30-day, 90-day trends
   └── Alert: score drops > 5% from 7-day rolling average

2. PROMPTFOO REGRESSION TESTING
   ├── 100 test cases per agent (client-configurable)
   ├── Runs weekly (or on-demand via dashboard button)
   ├── Compares results against baseline
   ├── Output: pass/fail per test + delta from baseline
   └── Dashboard shows: which specific behaviors changed

3. BEHAVIORAL DRIFT DETECTION (V1 UPGRADE — powered by Evidently AI)
   ├── Powered by: Evidently AI (evidently.ai) — production ML monitoring
   ├── Statistical drift detection on output distributions
   ├── Monitors: response length distribution, vocabulary patterns, 
   │   sentiment distribution, topic distribution
   ├── Explicit drift metrics (not "Evidently-style" — actual Evidently):
   │   ├── PSI (Population Stability Index) — overall distribution shift
   │   ├── KL Divergence — information-theoretic drift measurement
   │   ├── Wasserstein Distance — earth mover's distance for continuous features
   │   ├── JS Divergence — symmetric alternative to KL for robust comparison
   │   └── Custom thresholds per metric (configurable per agent)
   ├── Evidently Reports: auto-generated HTML drift reports (shareable)
   ├── Evidently Test Suites: pass/fail drift tests in CI/CD pipeline
   └── Alert: "Agent response length increased 40% — PSI: 0.32 (threshold: 0.20)"

4. BEHAVIORAL FINGERPRINTING
   ├── Generates a behavioral signature weekly
   ├── Embeds 100 representative responses → creates fingerprint vector
   ├── Compares this week's fingerprint to last week's
   ├── Large delta = behavioral shift, even if individual tests pass
   └── Catches "vibe shift" that individual tests miss

5. PROVIDER VERSION TRACKING
   ├── Monitors model version strings from API responses
   ├── Detects silent model updates (GPT-4o-2024-05-13 → GPT-4o-2024-08-06)
   ├── Correlates version changes with score changes
   └── Alert: "Model version changed 2 days ago. Consistency score dropped 8%."

TECHNOLOGY STACK:
  ├── lm-evaluation-harness — daily benchmark evaluation
  ├── promptfoo — regression test runner
  ├── Evidently AI — production drift detection (PSI, KL, Wasserstein, JS divergence)
  ├── Evidently Test Suites — automated drift pass/fail in CI/CD
  ├── text-embedding-3-large — behavioral fingerprint embeddings
  └── scikit-learn — statistical utilities for custom drift analysis
```

**Dashboard Output:**
```
CONSISTENCY ENGINE — LIVE VIEW
─────────────────────────────────────────────────────
Behavioral Stability Score: 76.8 / 100  ⚠️
Drift Detected:             YES — 14-day trend
Drift Magnitude:            -11.3% vs baseline
Regression Test Score:      82/100 (was 93/100 last week)
Root Cause:                 Model version changed: gpt-4-0613 → gpt-4-1106
Behavioral Fingerprint:     Δ 0.14 from last week (threshold: 0.10)

EVIDENTLY DRIFT METRICS:
  PSI (response length):    0.32  ⚠️ (threshold: 0.20)
  KL Divergence (topics):   0.18  ⚠️ (threshold: 0.15)
  Wasserstein (sentiment):  0.09  ✅ (threshold: 0.15)
  JS Divergence (vocab):    0.21  ⚠️ (threshold: 0.15)
  Drift Report:             [View Full Evidently Report →]

TREND:
  Week 1: 93  Week 2: 91  Week 3: 88  Week 4: 82 ⚠️ (declining)
  
Action: Review + re-test after model update. Evidently report shared with team.
─────────────────────────────────────────────────────
```

---

### 2.4 ENGINE 4: SYSTEM ENGINE (V1 Weight: 10%)

**What it does:** Monitors the AI system's infrastructure health.

```
CAPABILITIES IN V1:

1. LATENCY MONITORING
   ├── Tracks API response time per request
   ├── P50, P95, P99 latency metrics
   ├── Historical trend (hourly, daily, weekly)
   └── Alert: P95 latency > 5000ms for 5+ minutes

2. ERROR RATE TRACKING
   ├── HTTP error codes (429, 500, 503)
   ├── Timeout tracking
   ├── Error rate percentage (5-minute rolling window)
   └── Alert: error rate > 5% for 3+ minutes

3. COST MONITORING
   ├── Token usage per request (prompt + completion)
   ├── Estimated cost per request (based on model pricing)
   ├── Daily/monthly cost totals
   └── Alert: daily cost exceeds budget threshold

4. UPTIME / AVAILABILITY
   ├── Is the AI endpoint responding?
   ├── Health check every 60 seconds (configurable)
   ├── Uptime percentage (24h, 7d, 30d)
   └── Alert: endpoint unreachable for 2+ consecutive checks

5. THROUGHPUT
   ├── Requests per second/minute/hour
   ├── Queue depth (if applicable)
   └── Capacity utilization percentage

6. COST-PER-OUTCOME INTELLIGENCE (V1 UPGRADE)
   ├── Goes beyond "cost per request" → measures cost per SUCCESSFUL outcome
   ├── Tracks:
   │   ├── Cost per successful response (no hallucination, no safety flag)
   │   ├── Cost per failed response (hallucinated, blocked, or errored)
   │   ├── Waste ratio: failed_cost / total_cost (how much money is wasted?)
   │   └── Cost efficiency trend: are we getting better or worse over time?
   ├── Example dashboard insight:
   │   "You're spending $0.04/successful response but $0.12/failed response.
   │    18% of your budget ($847/month) is wasted on responses that fail quality checks."
   ├── Actionable: Links cost spikes to specific failure types
   │   "Cost spike on Tuesday: 40% increase caused by hallucination retries"
   └── Model comparison: Cost-per-successful-outcome across models
       "GPT-4o: $0.04/success | Claude-3-Sonnet: $0.03/success | Gemini: $0.025/success"

7. PERFORMANCE-QUALITY CORRELATION (V1 UPGRADE)
   ├── Correlates system metrics with trust metrics
   ├── Answers: "Does higher latency mean lower quality?"
   ├── Tracks:
   │   ├── Latency vs Trust Score correlation (per agent)
   │   ├── Error rate vs Hallucination rate correlation
   │   ├── Token count vs Response quality correlation
   │   └── Time-of-day patterns (quality drops during peak load?)
   ├── Dashboard insight:
   │   "Responses > 3s latency have 23% lower Trust Score on average"
   │   "Quality drops 15% between 2-4pm EST (peak traffic)"
   └── Why this matters: Helps clients understand if scaling issues = quality issues

TECHNOLOGY STACK:
  ├── LiteLLM — unified model API metrics
  ├── OpenLLMetry — OpenTelemetry instrumentation for LLMs
  ├── OTel spans ingested from client SDK
  ├── Custom aggregation in ClickHouse
  ├── Cost-per-outcome calculator (joins trust_events + cost data in ClickHouse)
  └── Correlation engine (ClickHouse materialized views for perf-quality analysis)
```

**Dashboard Output:**
```
SYSTEM ENGINE — LIVE VIEW
─────────────────────────────────────────────────────
System Health Score:        95.1 / 100
API Latency (P95):          1,247ms  ✅ (threshold: 5,000ms)
Error Rate (5min):          0.3%     ✅ (threshold: 5%)
Uptime (30d):               99.94%   ✅
Daily Cost:                 $47.20   ✅ (budget: $100)
Throughput:                 142 req/min

COST-PER-OUTCOME:
  Cost/successful response: $0.033   ✅
  Cost/failed response:     $0.097   ⚠️ (3x successful)
  Waste ratio:              12.4%    ($5.84 wasted today)
  Trend:                    ↓ improving (was 18.2% last week)

PERFORMANCE-QUALITY CORRELATION:
  Latency ↔ Trust Score:    r = -0.34 (moderate negative — higher latency = lower quality)
  Peak degradation:          2-4pm EST (quality drops 11% during peak)

MODEL USAGE:
  gpt-4o:          78% of traffic, avg 1,100ms, $0.033/success
  claude-3-sonnet: 22% of traffic, avg 1,400ms, $0.028/success
─────────────────────────────────────────────────────
```

---

## 3. TRUST SCORE V1 — COMPUTATION WITH 4 ENGINES

### 3.1 V1 Trust Score Formula

```
V1 TRUST SCORE = (
    0.30 × Safety_Score
  + 0.25 × Grounding_Score
  + 0.20 × Consistency_Score
  + 0.10 × System_Score
  + 0.15 × Coverage_Score
)

WHERE:
  Safety_Score:      0-100 from Safety Engine
  Grounding_Score:   0-100 from Grounding Engine
  Consistency_Score: 0-100 from Consistency Engine
  System_Score:      0-100 from System Engine
  Coverage_Score:    0-100 computed as:
    events_received_24h / expected_daily_events × 100
    Capped at 100.
    expected_daily_events = rolling 7-day average × 0.8 (allow 20% normal variance)

RESULT: 0–100 single number.
```

### 3.2 Override Rules (V1)

```
OVERRIDE RULES — THESE OVERRIDE THE FORMULA:

RULE 1: SAFETY FLOOR
  IF Safety_Score < 40 → Trust Score CANNOT exceed 50.
  No matter how good other engines are. Safety is non-negotiable.

RULE 2: CRITICAL INCIDENT OVERRIDE
  IF any Engine has an active CRITICAL severity incident
  → Trust Score drops by minimum 15 points from formula result.

RULE 3: SYSTEM DOWN OVERRIDE  
  IF System Engine detects endpoint unreachable
  → Trust Score = "UNAVAILABLE" (not a number — a status).
  Dashboard shows: "⚠️ AI endpoint not responding"

RULE 4: LOW COVERAGE PENALTY
  IF Coverage_Score < 50 (client sending < 50% of expected traffic)
  → Trust Score displays with caveat: "⚠️ LOW COVERAGE — score may not reflect full behavior"
  → Badge shows coverage warning (See Section 14)
```

### 3.3 Cold Start Handling

```
COLD START RULES:

Events received:  0-9     → NO SCORE displayed. Message: "Collecting data..."
Events received:  10-99   → Trust Score displayed with label: "PROVISIONAL"
                            (sample too small for statistical confidence)
Events received:  100-499 → Trust Score displayed with label: "BUILDING"
                            (score is converging, may shift significantly)
Events received:  500+    → Trust Score displayed normally. Full confidence.
                            (sufficient data for all 4 engine baselines)

PROVISIONAL → BUILDING → STABLE transitions are automatic.
Dashboard shows the label next to the Trust Score number.
```

### 3.4 Trust Score Status Bands

```
SCORE     STATUS       COLOR    MEANING
─────     ─────────    ──────   ─────────────────────────────────
90-100    TRUSTED      Green    AI is operating well across all dimensions
75-89     CAUTION      Amber    Minor issues detected, investigate recommended
60-74     AT RISK      Orange   Significant issues, action required
0-59      CRITICAL     Red      Serious problems, immediate action needed
```

### 3.5 V1 → V9 Migration Path

```
WHEN MORE ENGINES SHIP, TRUST SCORE RECALIBRATES:

V1 (4 engines):
  Safety: 30%  Grounding: 25%  Consistency: 20%  System: 10%  Coverage: 15%

V2 (6 engines — add Uncertainty + Context):
  Safety: 25%  Grounding: 18%  Consistency: 15%  System: 8%
  Uncertainty: 15%  Context: 10%  Coverage: 9%

V3 (9 engines — add Cognitive + Behavior + Focus):
  Safety: 20%  Grounding: 15%  Consistency: 12%  System: 6%
  Uncertainty: 15%  Context: 10%  Cognitive: 13%
  Behavior: 5%  Focus: 4%  (Coverage becomes part of Coverage Intelligence)

MIGRATION RULE:
  When a new engine ships, all clients get a "Trust Score Recalibration" email:
  "We've added [Engine Name]. Your Trust Score may shift slightly as the 
   new engine contributes its data. This is expected."
  Score normalization period: 3 days after each new engine activation.
```

---

## 4. TECHNOLOGY STACK — V1 ONLY

```
WHAT WE USE IN V1 AND WHY:

FRONTEND:
  Next.js 14 (App Router)     → Server-rendered dashboard, fast load
  Tailwind CSS + shadcn/ui    → Professional UI without custom CSS
  Recharts                    → Trust Score trend charts
  Socket.io (WebSocket)       → Real-time Trust Score updates
  Clerk                       → Authentication (email/password + MFA + magic link)
  Stripe.js                   → Billing integration on frontend

BACKEND — API LAYER:
  Fastify (Node.js)           → Main API server (REST endpoints)
  Kong                        → API Gateway (rate limiting, routing, auth)
  
BACKEND — ENGINE WORKERS:
  Python / FastAPI            → Engine computation workers (each engine = 1 microservice)
  guardrails-ai               → Safety Engine validators (PII, toxicity, injection)
  NeMo Guardrails             → 5-rail safety system
  promptfoo                   → Red team signatures + regression testing
  lm-evaluation-harness       → Consistency Engine daily benchmarks
  Phoenix (Arize)             → Grounding Engine RAG evaluation
  Langfuse                    → LLM-as-judge pipeline (Grounding + Safety scoring)
  Ragas                       → Claim-level attribution + RAG quality metrics (Grounding Engine)
  DeepEval                    → Hallucination scoring + contextual relevancy (Grounding Engine)
  Evidently AI                → Production drift detection — PSI, KL, Wasserstein, JS (Consistency Engine)
  scikit-learn                → Statistical utilities for drift analysis (Consistency Engine)
  Llama-3-8B (vLLM)          → LLM Safety Judge for subtle attack detection (Safety Engine)
  LiteLLM                     → Unified model API (System Engine metrics)
  OpenLLMetry                 → OpenTelemetry for LLMs

DATABASES:
  PostgreSQL 15 (Cloud SQL)   → Operational data (clients, agents, incidents)
  ClickHouse (Altinity on GKE)→ Analytics data (trust_events — billions of rows)
  Redis (Cloud Memorystore)   → Cache (Trust Score, rate limits, sessions)
  BigQuery                    → Long-term aggregation (monthly summaries)

INFRASTRUCTURE:
  GCP / GKE                   → Kubernetes cluster (auto-scaling)
  Cloud Pub/Sub               → Event queue (1 topic per engine)
  Terraform                   → Infrastructure-as-code (all resources)
  Cloud Build + GitHub Actions→ CI/CD pipeline
  Google Secret Manager       → Secrets storage (API keys, tokens)
  Cloud Armor                 → WAF + DDoS protection
  Cloud Load Balancer         → Global HTTPS load balancing

MESSAGING & ALERTS:
  SendGrid                    → Email alerts
  Slack API                   → Slack alerts (webhook-based)
  Stripe                      → Billing + subscription management

MONITORING (ZROKY's own infra):
  Prometheus + Grafana        → Internal metrics
  Cloud Logging               → Centralized logs

NOT IN V1:
  ❌ D3.js (needed for Behavior Engine network graphs — V3)
  ❌ TransformerLens (Cognitive Engine — V3)
  ❌ Pinecone (Focus Engine purpose vector — V2)
  ❌ vLLM / GPU nodes (Cognitive Engine open-weight analysis — V3)
     EXCEPTION: vLLM IS needed for Health Check Llama-3-8B judge (Cloud Run, separate)
```

---

## 5. DATABASE SCHEMA — V1 TABLES ONLY

### 5.1 PostgreSQL — Operational Data

```sql
-- CLIENTS TABLE
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  plan_id UUID REFERENCES subscription_plans(id),
  tier ENUM('developer', 'smb', 'growth', 'enterprise') NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  status ENUM('active', 'trial', 'suspended', 'churned') DEFAULT 'trial',
  slack_workspace_id VARCHAR(100),
  slack_bot_token TEXT,  -- AES-256-GCM encrypted at app layer (pgcrypto)
  badge_enabled BOOLEAN DEFAULT FALSE,
  badge_verified_domains TEXT[],  -- ['acme.com', 'app.acme.com']
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI AGENTS TABLE
CREATE TABLE ai_agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  name VARCHAR(255) NOT NULL,
  type ENUM('chatbot', 'rag', 'autonomous_agent', 'multi_agent') NOT NULL,
  provider VARCHAR(100),      -- 'openai', 'anthropic', 'google', 'ollama'
  model_name VARCHAR(100),
  api_endpoint TEXT,
  integration_type ENUM('sdk', 'proxy', 'webhook') NOT NULL,
  trust_score_threshold INTEGER DEFAULT 75,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ
);

-- API KEYS TABLE
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  key_hash VARCHAR(64) NOT NULL,    -- HMAC-SHA256 hash (key never stored raw)
  key_prefix VARCHAR(12) NOT NULL,  -- First 12 chars shown in dashboard
  key_type ENUM('ingest', 'manage', 'agent') NOT NULL,
  scopes TEXT[] DEFAULT '{}',       -- ['read:trust_score', 'write:events']
  last_used_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  revoked_at TIMESTAMPTZ
);

-- ALERT RULES TABLE
CREATE TABLE alert_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  agent_id UUID REFERENCES ai_agents(id),
  engine VARCHAR(50) NOT NULL,      -- 'safety', 'grounding', etc.
  condition_type ENUM('threshold', 'drift', 'anomaly') NOT NULL,
  threshold_value NUMERIC(5,2),
  notification_channels JSONB,      -- {'slack': true, 'email': true}
  severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
  enabled BOOLEAN DEFAULT TRUE
);

-- USERS TABLE
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  email VARCHAR(255) UNIQUE NOT NULL,
  role ENUM('owner', 'admin', 'engineer', 'analyst', 'viewer') NOT NULL,
  clerk_user_id VARCHAR(100),       -- Clerk external ID
  last_login TIMESTAMPTZ,
  mfa_enabled BOOLEAN DEFAULT FALSE
);

-- INCIDENTS TABLE
CREATE TABLE incidents (
  id VARCHAR(20) PRIMARY KEY,       -- 'INC-2026-089'
  client_id UUID NOT NULL REFERENCES clients(id),
  agent_id UUID NOT NULL REFERENCES ai_agents(id),
  engine VARCHAR(50) NOT NULL,
  severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  evidence JSONB,
  trust_score_at_incident NUMERIC(5,2),
  engine_score_at_incident NUMERIC(5,2),
  status ENUM('open', 'investigating', 'resolved', 'dismissed') DEFAULT 'open',
  assigned_to UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ,
  resolution_notes TEXT,
  slack_thread_ts VARCHAR(50),
  alert_sent_slack BOOLEAN DEFAULT FALSE,
  alert_sent_email BOOLEAN DEFAULT FALSE
);

CREATE INDEX ix_incidents_client_created ON incidents (client_id, created_at DESC);
CREATE INDEX ix_incidents_status ON incidents (status, severity);

-- SUBSCRIPTION PLANS TABLE
CREATE TABLE subscription_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(50) NOT NULL UNIQUE,
  max_agents INTEGER,
  max_interactions_month BIGINT,
  max_users INTEGER,
  data_retention_days INTEGER DEFAULT 3,
  price_monthly_usd NUMERIC(10,2),
  price_annual_usd NUMERIC(10,2),
  features JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- WEBHOOK ENDPOINTS TABLE (V1 outbound webhooks)
CREATE TABLE webhook_endpoints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  url TEXT NOT NULL,
  secret VARCHAR(64) NOT NULL,        -- HMAC signing secret
  events TEXT[] NOT NULL,              -- ['incident.created', 'trust_score.changed']
  enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- HEALTH CHECK SCANS TABLE (for zroky.ai/scan)
CREATE TABLE health_check_scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255),                 -- NULL for first scan (no email required)
  user_id UUID REFERENCES users(id),  -- NULL for anonymous scans
  ip_hash VARCHAR(64) NOT NULL,       -- Hashed IP for rate limiting, not raw IP
  scan_type ENUM('api_endpoint', 'api_key', 'csv_upload') NOT NULL,
  overall_score NUMERIC(5,2),
  safety_score NUMERIC(5,2),
  accuracy_score NUMERIC(5,2),
  consistency_score NUMERIC(5,2),
  findings_count INTEGER DEFAULT 0,
  critical_findings_count INTEGER DEFAULT 0,
  report_url TEXT,                    -- Unique URL to access report for 30 days
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ              -- Auto-delete after 30 days
);

CREATE INDEX ix_scans_ip_created ON health_check_scans (ip_hash, created_at DESC);
```

### 5.2 ClickHouse — Analytics Data

```sql
-- TRUST EVENTS TABLE (Main analytics — V1 has 4 engine columns)
CREATE TABLE trust_events (
  event_id String,
  client_id String,
  agent_id String,
  timestamp DateTime64(3),
  -- V1 Engine Scores
  safety_score Float32,
  grounding_score Float32,
  consistency_score Float32,
  system_score Float32,
  coverage_score Float32,
  total_trust_score Float32,
  -- V2+ Engine Scores (nullable columns — added later, backfill-friendly)
  uncertainty_score Nullable(Float32),
  cognitive_score Nullable(Float32),
  context_score Nullable(Float32),
  behavior_score Nullable(Float32),
  focus_score Nullable(Float32),
  -- AI interaction metadata
  model_name LowCardinality(String),
  prompt_tokens UInt32,
  completion_tokens UInt32,
  latency_ms UInt32,
  cost_usd Float32,
  -- Context
  session_id String,
  user_segment LowCardinality(String),
  -- Flags
  safety_alert_triggered UInt8,
  alert_type LowCardinality(String)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (client_id, agent_id, timestamp)
TTL timestamp + INTERVAL 24 MONTH;
```

### 5.3 Redis — Cache Layer (V1 Keys)

```
Key Schema:
  trust_score:{client_id}:{agent_id}   → JSON  (TTL: 60s)
  engine_scores:{client_id}:{agent_id} → JSON  (TTL: 60s)
  alert_count:{client_id}:24h          → Int   (TTL: 24h)
  api_rate_limit:{api_key_hash}        → Int   (TTL: 1min)
  client_config:{client_id}            → JSON  (TTL: 5min)
  badge_score:{agent_id}               → JSON  (TTL: 30s)
  scan_rate:{ip_hash}                  → Int   (TTL: 24h)
```

---

## 6. GCP INFRASTRUCTURE — V1 DEPLOYMENT

```
V1 INFRASTRUCTURE — SINGLE REGION TO START:

REGION: us-central1 (Iowa)
  WHY: Lowest latency for majority of initial users (US + Europe acceptable)
  EU region (europe-west4) added in Phase 3 for GDPR

GKE CLUSTER: zroky-production
  ├── api-pool:    n2-standard-8 (8 vCPU, 32GB) × 3-15 nodes (auto-scale)
  ├── engine-pool: n2-standard-8 (8 vCPU, 32GB) × 3-20 nodes (auto-scale)  
  └── frontend-pool: n2-standard-4 (4 vCPU, 16GB) × 2-5 nodes (auto-scale)
  
  NOTE: V1 uses n2-standard-8 (not n2-standard-16) for engine workers.
  At V1 scale (< 1,000 clients), 8 vCPU per node is sufficient.
  Scale to n2-standard-16 when sustained load requires it.

DATABASES:
  ├── Cloud SQL (PostgreSQL 15): db-n1-standard-4, private IP, HA failover
  ├── ClickHouse: Single node on GKE to start (Altinity Operator)
  │   Scale to 3-node cluster at 100M+ events
  ├── Redis (Cloud Memorystore): M1 tier (1GB), scale to M3 as needed
  └── BigQuery: On-demand pricing (no reservation needed for V1 volume)

PUB/SUB TOPICS (V1 — 4 engines + shared):
  ├── zroky-events-safety
  ├── zroky-events-grounding
  ├── zroky-events-consistency
  ├── zroky-events-system
  ├── zroky-events-dead-letter     (failed messages)
  └── zroky-events-trust-score     (aggregated scores for dashboard push)

CLOUD RUN (Health Check only):
  ├── zroky-health-check-scanner   (serverless, scale-to-zero)
  └── Separate from main GKE cluster (scan traffic ≠ production traffic)

CLOUD RUN (vLLM Judge for Health Check):
  └── llama-3-8b-judge             (GPU-enabled Cloud Run or GKE GPU node pool)

ESTIMATED V1 MONTHLY INFRA COST:
  GKE (3 pools, auto-scale): $1,500-3,000/month
  Cloud SQL:                  $200-400/month
  ClickHouse node:            $300-500/month
  Redis:                      $100-200/month
  Cloud Pub/Sub:              $50-100/month
  Cloud Run (health check):   $100-500/month (depends on scan volume)
  Load Balancer + Armor:      $100-200/month
  BigQuery:                   $50-100/month
  Misc (logging, monitoring): $100-200/month
  ──────────────────────────────────────────
  TOTAL:                      $2,500-5,200/month
  
  At 50 paying clients ($99 avg): $4,950 MRR. Breakeven at ~50 clients.
  At 200 paying clients: $19,800 MRR. Healthy margin.
```

### 6.1 Deployment Pipeline (V1)

```
DEVELOPER → GITHUB PUSH → GITHUB ACTIONS:
  ├── Lint + type check
  ├── Unit tests (Jest for Node, Pytest for Python)
  ├── Security scan (Snyk)
  ├── Docker image build + push to Artifact Registry
  └── IF main branch:
      ├── Deploy to STAGING (auto)
      ├── Run E2E tests (Playwright)
      ├── IF all pass → Deploy to PRODUCTION (blue-green)
      │   ├── New pods (green) deploy alongside old (blue)
      │   ├── Traffic shift: 5% → 25% → 100% over 10 minutes
      │   └── Auto-rollback if error rate > 1%
      └── Slack notification to #deployments
```

---

## 7. API — V1 ENDPOINTS ONLY

### 7.1 Design Principles (from Master Blueprint Section 6)

```
V1 FOLLOWS ALL 10 ENTERPRISE API LAWS:

 1. ONE RESPONSE ENVELOPE    — Same JSON shape everywhere
 2. SPLIT API KEYS           — Ingest keys can't read. Read keys can't ingest.
 3. CURSOR PAGINATION        — Every list endpoint
 4. IDEMPOTENCY              — Every POST has Idempotency-Key header
 5. STRUCTURED ERRORS        — Error code + human message + docs link
 6. RATE LIMITING VIA HEADERS— X-RateLimit-* on every response
 7. WEBHOOK SIGNATURES       — HMAC-SHA256 on every outbound webhook
 8. VERSIONING VIA HEADER    — ZROKY-Version: 2026-04-08
 9. SANDBOX ENVIRONMENT      — sandbox.ingest.zroky.ai (fake data, same contract)
10. OPENAPI SPEC             — Auto-generated, always current
```

### 7.2 Domains

```
V1 DOMAINS:

PRODUCTION:
  ingest.zroky.ai         → Event ingestion (write-only)
  api.zroky.ai            → Query + Management (read + manage)
  stream.zroky.ai         → WebSocket (real-time dashboard updates)
  badge.zroky.ai          → Badge score API (public, no auth)

SANDBOX:
  sandbox.ingest.zroky.ai → Sandbox ingestion
  sandbox.api.zroky.ai    → Sandbox query + management

HEALTH CHECK:
  zroky.ai/scan           → Health Check UI (Next.js page)
  scan-api.zroky.ai       → Health Check backend (Cloud Run)
```

### 7.3 Authentication — Split API Keys

```
KEY TYPES:

zk_ingest_*   → Write-only. Can POST events. Cannot read scores, manage agents.
zk_manage_*   → Read + manage. Can GET scores, CRUD agents. Cannot POST events.
zk_agent_*    → Scoped to single agent. Can ingest + read for that agent only.

VALIDATION:
  Authorization: Bearer zk_ingest_Xn29mKs84nL...
  → Server HMAC-SHA256 hashes the key
  → Compares against api_keys.key_hash in Redis cache
  → Checks key_type matches endpoint requirement
  → Increments rate limit counter

MAX KEYS: 5 active per client (any type).
ROTATION: Create new key → old key has 24h grace period → revoke old.
```

### 7.4 Universal Response Envelope

```json
// SUCCESS
{
  "ok": true,
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-04-08T14:00:00Z",
    "version": "2026-04-08"
  }
}

// ERROR
{
  "ok": false,
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Retry after 12 seconds.",
    "doc_url": "https://docs.zroky.ai/errors/rate_limit_exceeded",
    "retry_after": 12
  },
  "meta": {
    "request_id": "req_abc124",
    "timestamp": "2026-04-08T14:00:01Z",
    "version": "2026-04-08"
  }
}

// LIST (paginated)
{
  "ok": true,
  "data": [ ... ],
  "pagination": {
    "has_more": true,
    "next_cursor": "cur_xyz789"
  },
  "meta": { ... }
}
```

### 7.5 V1 Endpoint Directory

```
INGESTION API (ingest.zroky.ai) — requires zk_ingest_* or zk_agent_* key

  POST /v1/events
    Body: { agent_id, prompt, response, model, metadata, session_id }
    Response: { event_id, status: "accepted" }
    Latency target: < 10ms (async — event queued to Pub/Sub)
    Idempotency: Idempotency-Key header (24h window)

  POST /v1/events/batch
    Body: { events: [ ...up to 1,000 ] }
    Response: { accepted: 987, rejected: 13, errors: [...] }
    Latency target: < 50ms

QUERY API (api.zroky.ai) — requires zk_manage_* or zk_agent_* key

  GET /v1/trust-score/{agent_id}
    Response: { score, status, engines: { safety, grounding, consistency, system },
                coverage: { score, band }, last_event_at, cold_start_label }

  GET /v1/trust-score/{agent_id}/history
    Params: ?period=30d&granularity=1h
    Response: { data_points: [ { timestamp, score, engines } ] }

  GET /v1/incidents
    Params: ?agent_id=&status=open&severity=critical&cursor=&limit=50
    Response: paginated list of incidents

  GET /v1/incidents/{incident_id}
    Response: full incident detail with evidence + timeline

MANAGEMENT API (api.zroky.ai) — requires zk_manage_* key

  POST   /v1/agents           → Create agent
  GET    /v1/agents           → List agents (paginated)
  GET    /v1/agents/{id}      → Get agent detail
  PATCH  /v1/agents/{id}      → Update agent config
  DELETE /v1/agents/{id}      → Soft-delete agent

  POST   /v1/alert-rules      → Create alert rule
  GET    /v1/alert-rules      → List rules
  PATCH  /v1/alert-rules/{id} → Update rule
  DELETE /v1/alert-rules/{id} → Delete rule

  POST   /v1/api-keys         → Create new API key
  GET    /v1/api-keys         → List keys (shows prefix only)
  DELETE /v1/api-keys/{id}    → Revoke key

  POST   /v1/webhooks         → Register webhook endpoint
  GET    /v1/webhooks         → List webhooks
  PATCH  /v1/webhooks/{id}    → Update webhook
  DELETE /v1/webhooks/{id}    → Delete webhook
  POST   /v1/webhooks/{id}/test → Send test event to webhook

BADGE API (badge.zroky.ai) — PUBLIC, no auth required

  GET /v1/score/{agent_id}
    Response: { score, status, coverage, last_event_at, account_active,
                verified_domain, badge_enabled, signature }
    Cache: Redis TTL 30s, CDN edge-cached 30s
```

### 7.6 Rate Limits (V1)

```
TIER              INGEST          QUERY           MANAGEMENT
Developer (free)  100/min         60/min          30/min
SMB ($99)         1,000/min       300/min         100/min
Growth ($499)     10,000/min      1,000/min       300/min
Enterprise        100,000/min     10,000/min      1,000/min

Headers on every response:
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 847
  X-RateLimit-Reset: 1712581200
```

---

## 8. DASHBOARD — V1 VIEWS ONLY

### 8.1 SMB Simplified View (Default for Developer + SMB)

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ZROKY Dashboard — Acme Corp                                        │
│                                                                      │
│  ┌─────────────────────────────────┐  ┌──────────────────────────┐  │
│  │     TRUST SCORE                 │  │  ALERT FEED              │  │
│  │                                 │  │                          │  │
│  │         87                      │  │  🔴 Prompt injection     │  │
│  │       ─────                     │  │     detected (2 min ago) │  │
│  │     CAUTION 🟡                  │  │                          │  │
│  │                                 │  │  🟡 Grounding score      │  │
│  │  Coverage: 94% ✅               │  │     dropped 8% (1h ago)  │  │
│  │  Label: STABLE                  │  │                          │  │
│  │                                 │  │  🟢 Model version change │  │
│  │  ┌──────────────────────────┐   │  │     detected (6h ago)    │  │
│  │  │  30-day trend chart      │   │  │                          │  │
│  │  │  ████████████ 87         │   │  │  [View All Alerts →]     │  │
│  │  │  █████████── 82          │   │  └──────────────────────────┘  │
│  │  │  ████████████████ 91     │   │                                │
│  │  └──────────────────────────┘   │  ┌──────────────────────────┐  │
│  └─────────────────────────────────┘  │  4-ENGINE SCORES         │  │
│                                       │                          │  │
│                                       │  Safety:      91 ✅       │  │
│                                       │  Grounding:   79 ⚠️      │  │
│                                       │  Consistency: 88 ✅       │  │
│                                       │  System:      95 ✅       │  │
│                                       │                          │  │
│                                       │  [Deep Dive →]           │  │
│                                       └──────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.2 Engineer View (Available to all tiers — default for Growth)

```
┌──────────────────────────────────────────────────────────────────────┐
│  ZROKY Engineer View — Acme Corp — Customer Support Agent           │
│                                                                      │
│  Trust Score: 87 🟡 CAUTION    Coverage: 94% ✅    Status: STABLE   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ ENGINE         SCORE   TREND (7d)   INCIDENTS   STATUS        │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │ Safety         91      ████████████  2 open     ✅ HEALTHY    │  │
│  │ Grounding      79      ██████████──  1 open     ⚠️ DEGRADED   │  │
│  │ Consistency    88      ████████████  0          ✅ HEALTHY    │  │
│  │ System         95      ████████████  0          ✅ HEALTHY    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──── INCIDENT DETAIL (INC-2026-014) ────────────────────────────┐ │
│  │ Engine: Grounding | Severity: HIGH | Status: INVESTIGATING     │ │
│  │ Title: Retrieval relevance dropped 15% for pricing queries     │ │
│  │                                                                 │ │
│  │ Evidence:                                                       │ │
│  │   Before: 92% retrieval relevance (7-day avg)                  │ │
│  │   Now:    77% retrieval relevance                               │ │
│  │   Affected queries: "pricing", "cost", "plan comparison"        │ │
│  │                                                                 │ │
│  │ Suggested Action:                                               │ │
│  │   Product pricing page was updated 3 days ago but vector DB     │ │
│  │   embeddings were not re-indexed.                               │ │
│  │   [Re-embed Now] [Run Test Suite] [Dismiss]                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──── TRUST SCORE HISTORY (30 days) ─────────────────────────────┐ │
│  │  100 ┤                                                          │ │
│  │   90 ┤  ████████████████████████████████                        │ │
│  │   80 ┤              ██████████████████████                      │ │
│  │   70 ┤                                                          │ │
│  │   60 ┤                                                          │ │
│  │      └──────────────────────────────────────────── days →       │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.3 Executive View (Growth + Enterprise only)

```
┌──────────────────────────────────────────────────────────────────────┐
│  ZROKY Executive View — Acme Corp Portfolio                          │
│                                                                      │
│  PORTFOLIO TRUST SCORE: 84 🟡    AGENTS: 3 active                   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ AGENT              SCORE   STATUS     TREND   INCIDENTS       │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │ Customer Support    87     CAUTION    ↗       3 open          │  │
│  │ Fraud Detection     91     TRUSTED    →       0               │  │
│  │ Loan Advisor        74     AT RISK    ↘       7 open          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──── 30-DAY TREND (ALL AGENTS) ──────────────────────────────────┐│
│  │  [Line chart: 3 colored lines, one per agent, 30-day period]    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  KEY METRICS:                                                        │
│  Total Events (30d): 2.4M   Total Incidents: 10   Resolved: 7       │
│  Worst Engine: Grounding (avg 79 across all agents)                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 8.4 Design System

```
V1 DESIGN RULES:

COLORS:
  Primary:     #000000 (Pure Black)
  Secondary:   #FFFFFF (Pure White)
  Gray:        #888888 (Medium Gray)
  Light Gray:  #F5F5F5 (Background)
  Accent:      #0066FF (Electric Blue — critical alerts ONLY)

STATUS COLORS:
  Trusted (90-100):  #22C55E (Green)
  Caution (75-89):   #F59E0B (Amber)
  At Risk (60-74):   #F97316 (Orange)
  Critical (0-59):   #EF4444 (Red)

TYPOGRAPHY:
  Headings:   Inter (bold)
  Body:       Inter (regular)
  Monospace:  JetBrains Mono (code, scores, IDs)

COMPONENTS: shadcn/ui (dark mode default)
  ├── Tables: DataTable with sorting, filtering, pagination
  ├── Charts: Recharts (line, bar, area)
  ├── Cards: shadcn Card component
  ├── Modals: shadcn Dialog
  ├── Toasts: shadcn Toast (bottom-right)
  └── Loading: Skeleton components (no spinners)

REAL-TIME:
  Trust Score number updates via WebSocket (no page refresh)
  Alert feed updates via WebSocket (push from server)
  Charts update every 60 seconds (poll, not WebSocket — too heavy for charts)
```

---

## 9. ONBOARDING FLOW — SIGNUP TO TRUST SCORE IN 15 MIN

```
SMB ONBOARDING FLOW (TOTAL: ~15 MINUTES):

STEP 1: SIGN UP (2 minutes)
  ├── Visit zroky.ai/signup
  ├── Enter: name, email, company name, password
  ├── Clerk handles auth (email verification, MFA optional)
  ├── Auto-created: client record, default Developer plan
  └── Redirected to: Dashboard → "Connect Your First AI Agent"

STEP 2: CHOOSE PLAN (1 minute)  
  ├── Show 4 plans side by side (Developer free, SMB $99, Growth $499, Enterprise)
  ├── "Start with Developer (free)" is pre-selected
  ├── SMB has "Start 14-day free trial" button
  ├── Stripe Checkout for SMB/Growth
  └── Enterprise → "Contact Sales" button

STEP 3: CONNECT YOUR AI (5 minutes)
  ├── Choose integration method:
  │   
  │   OPTION A: SDK (recommended)
  │   ├── "pip install zroky" or "npm install @zroky/sdk"
  │   ├── Copy-paste 5 lines of code:
  │   │   from zroky import ZROKYMonitor
  │   │   monitor = ZROKYMonitor(api_key="zk_ingest_...", agent_id="...")
  │   │   # Wrap your AI call:
  │   │   response = monitor.track(
  │   │       prompt=user_message, response=ai_response, model="gpt-4o"
  │   │   )
  │   └── Dashboard shows: "Waiting for first event..."
  │
  │   OPTION B: LangChain integration
  │   ├── from zroky.integrations.langchain import ZROKYCallbackHandler
  │   ├── handler = ZROKYCallbackHandler(api_key="...", agent_id="...")
  │   ├── chain.invoke(input, config={"callbacks": [handler]})
  │   └── Automatically captures all LangChain events
  │
  │   OPTION C: REST API (direct)
  │   ├── POST https://ingest.zroky.ai/v1/events
  │   ├── Headers: Authorization: Bearer zk_ingest_...
  │   ├── Body: { "agent_id": "...", "prompt": "...", "response": "...", "model": "gpt-4o" }
  │   └── For any language/framework without an SDK
  │
  └── "Test Connection" button: sends a test event, confirms receipt

STEP 4: SEE YOUR TRUST SCORE (6 minutes)
  ├── After first event: "1 event received!" toast notification
  ├── After 10 events: Trust Score appears with "PROVISIONAL" label
  ├── Dashboard auto-refreshes via WebSocket
  ├── First engine scores visible within 60 seconds
  ├── Email sent: "Your first Trust Score is ready: 82 🟡 CAUTION"
  └── In-app prompt: "Set up Slack alerts?" (if Growth plan)

STEP 5: CONFIGURE ALERTS (2 minutes)
  ├── Default alerts created automatically:
  │   ├── Trust Score drops below 70 → Email alert
  │   ├── Safety Engine critical incident → Email alert
  │   └── System down → Email alert
  ├── Growth+: "Connect Slack" button → OAuth flow → channel selection
  └── Custom alert rules via Alert Rules page
```

---

## 10. SDK — V1 CLIENT LIBRARIES

### 10.1 Python SDK

```python
# pip install zroky

from zroky import ZROKYMonitor

# Initialize
monitor = ZROKYMonitor(
    api_key="zk_ingest_Xn29mKs84nL...",
    agent_id="agent_abc123",
    # Optional config:
    fail_open=True,          # If ZROKY is down, AI keeps working (default: True)
    batch_size=50,           # Buffer events, send in batches (default: 50)
    flush_interval=5.0,      # Flush every 5 seconds (default: 5.0)
    max_queue_size=10000,    # Max events in local queue (default: 10000)
)

# Track a single interaction
result = monitor.track(
    prompt="What's the refund policy?",
    response="Our refund policy allows returns within 30 days...",
    model="gpt-4o",
    session_id="sess_xyz",           # Optional: group by conversation
    metadata={"user_tier": "premium"} # Optional: custom metadata
)

# Flush on shutdown (sends remaining buffered events)
monitor.flush()
monitor.close()
```

### 10.2 Python SDK — LangChain Integration

```python
from zroky.integrations.langchain import ZROKYCallbackHandler

handler = ZROKYCallbackHandler(
    api_key="zk_ingest_...",
    agent_id="agent_abc123"
)

# Works with any LangChain chain/agent
chain = prompt | llm | parser
result = chain.invoke(
    {"query": "What's the refund policy?"},
    config={"callbacks": [handler]}
)
# ZROKY automatically captures: prompt, response, model, latency, tokens
```

### 10.3 Node.js SDK

```typescript
// npm install @zroky/sdk

import { ZROKYMonitor } from '@zroky/sdk';

const monitor = new ZROKYMonitor({
  apiKey: 'zk_ingest_Xn29mKs84nL...',
  agentId: 'agent_abc123',
  failOpen: true,       // AI keeps working if ZROKY is down
  batchSize: 50,
  flushIntervalMs: 5000,
});

// Track interaction
await monitor.track({
  prompt: "What's the refund policy?",
  response: "Our refund policy allows returns within 30 days...",
  model: 'gpt-4o',
  sessionId: 'sess_xyz',
  metadata: { userTier: 'premium' },
});

// Graceful shutdown
await monitor.close();
```

### 10.4 SDK Design Principles

```
SDK RULES — NON-NEGOTIABLE:

1. FAIL-OPEN ALWAYS
   ├── If ZROKY API is unreachable → events queue locally in memory
   ├── Background thread retries every 30 seconds
   ├── If local queue exceeds max_queue_size → oldest events dropped (FIFO)
   ├── The client's AI NEVER stops working because of ZROKY
   └── Circuit breaker: after 5 consecutive failures, stop trying for 60s

2. ASYNC BY DEFAULT
   ├── monitor.track() returns immediately (< 1ms)
   ├── Event is added to in-memory queue
   ├── Background thread batches and sends to ZROKY API
   └── Zero latency added to the client's AI response time

3. TINY FOOTPRINT
   ├── Python SDK: < 500KB, 0 heavy dependencies
   ├── Node SDK: < 200KB, 0 heavy dependencies
   └── No ML models bundled (those run server-side)

4. ZERO CONFIGURATION NEEDED
   ├── Only required: api_key + agent_id
   ├── Everything else has sensible defaults
   └── Works out of the box with default settings
```

---

## 11. ALERTS — V1 NOTIFICATION SYSTEM

```
V1 ALERT CHANNELS:

1. EMAIL (ALL TIERS)
   ├── Via SendGrid
   ├── Triggered on: incidents, Trust Score threshold, system down
   ├── Format: Clean HTML email with Trust Score, engine, incident detail
   ├── Unsubscribe link (per-alert-type granularity)
   └── Delivery SLA: < 60 seconds from trigger

2. SLACK (GROWTH + ENTERPRISE ONLY)
   ├── OAuth 2.0 integration (user connects via dashboard)
   ├── Alerts posted to chosen channel(s)
   ├── Format: Rich Slack blocks with:
   │   ├── Trust Score + status emoji
   │   ├── Engine that triggered the alert
   │   ├── Incident ID + severity
   │   └── "View in Dashboard" button (Slack button → deep link)
   └── Multi-channel: route different severities to different channels
       e.g., critical → #ai-emergency, low → #ai-monitoring

3. IN-DASHBOARD ALERT CENTER
   ├── Real-time feed (WebSocket push)
   ├── Filter by: severity, engine, agent, status
   ├── Click to expand → full incident detail
   └── Mark as read / acknowledge / assign

4. WEBHOOKS (ALL TIERS)
   ├── Client registers endpoint URL
   ├── ZROKY sends POST with HMAC-SHA256 signed payload
   ├── Events: incident.created, incident.resolved, trust_score.changed,
   │          trust_score.critical, safety.campaign_detected
   ├── Retry policy: 3 retries with exponential backoff (1s, 10s, 60s)
   └── Webhook delivery log in dashboard (success/fail per delivery)

DEFAULT ALERT RULES (auto-created on signup):
  ├── Trust Score < 70 → Email (all tiers) + Slack (Growth+)
  ├── Safety incident (critical) → Email + Slack
  ├── System down (endpoint unreachable) → Email + Slack
  └── Coverage drops below 50% → Email
```

---

## 12. OPEN-SOURCE STRATEGY — WHAT SHIPS OPEN ON DAY 1

### 12.1 Repository Structure

```
github.com/zroky-ai/zroky-oss

zroky-oss/
├── sdk/                              ← MIT LICENSE
│   ├── python/                       ← pip install zroky
│   │   ├── zroky/
│   │   │   ├── __init__.py
│   │   │   ├── client.py             ← ZROKY Cloud API client
│   │   │   ├── monitor.py            ← Main monitoring wrapper
│   │   │   ├── fail_open.py          ← Circuit breaker + local queue
│   │   │   └── integrations/
│   │   │       ├── langchain.py      ← ZROKYCallbackHandler
│   │   │       ├── langraph.py       ← ZROKYGraph wrapper
│   │   │       └── openai.py         ← OpenAI client wrapper
│   │   └── setup.py
│   ├── node/                         ← npm install @zroky/sdk
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── client.ts
│   │   │   ├── monitor.ts
│   │   │   └── integrations/
│   │   │       ├── vercel-ai.ts      ← Vercel AI SDK hook
│   │   │       └── langchain.ts
│   │   └── package.json
│   └── go/                           ← Stub client (basic only)
│       └── zroky/client.go
│
├── safety-engine/                    ← BSL (Business Source License)
│   ├── detectors/
│   │   ├── prompt_injection.py
│   │   ├── jailbreak.py
│   │   ├── pii_scanner.py
│   │   ├── data_extraction.py
│   │   └── toxicity.py
│   ├── red_team/
│   │   └── signatures/
│   │       ├── injection_v1.yaml
│   │       ├── jailbreak_v1.yaml
│   │       └── extraction_v1.yaml
│   ├── scorer.py                     ← Basic safety score (0-100)
│   └── README.md
│
├── examples/
│   ├── python/
│   │   ├── basic_monitoring.py       ← 5-line quickstart
│   │   ├── langchain_with_zroky.py
│   │   └── fastapi_middleware.py
│   ├── node/
│   │   ├── nextjs_example/
│   │   └── express_example/
│   └── go/basic_example.go
│
├── docs/
│   ├── quickstart.md
│   ├── sdk-reference.md
│   ├── safety-engine-guide.md
│   └── migration-to-cloud.md        ← OSS → Cloud upsell path
│
├── LICENSE-SDK                       ← MIT License
├── LICENSE-SAFETY-ENGINE             ← BSL License
├── CONTRIBUTING.md
└── README.md                         ← Critical: quickstart + GIF + comparison table
```

### 12.2 License Strategy

```
MIT LICENSE — SDKs + All Integrations:
  ✅ Anyone can use, modify, redistribute commercially
  ✅ Zero friction for adoption
  ✅ Framework ecosystem expects MIT
  
BSL (Business Source License) — Safety Engine:
  ✅ Anyone can read, audit, use for their own company
  ✅ Anyone can contribute PRs
  ❌ CANNOT offer as hosted service to third parties
  ❌ CANNOT bundle into competing commercial product
  → Converts to Apache 2.0 after 3 years

NEVER OPEN-SOURCED (Proprietary):
  ├── Trust Score computation algorithm
  ├── All engines except Safety (Grounding, Consistency, System, etc.)
  ├── Dashboard + all frontend code
  ├── Coverage Intelligence
  └── All future proprietary engines (Behavior, Cognitive, Focus)
```

### 12.3 What OSS Users Get vs Cloud

```
                              OSS (Free)    Cloud (Paid)
SAFETY:
  Prompt injection detection    ✅              ✅
  Jailbreak detection           ✅              ✅
  PII scanning + redaction      ✅              ✅
  Safety score (0-100)          ✅ (local)      ✅ (cloud)

TRUST SCORE:
  4-engine weighted scoring     ❌              ✅
  Override Rules                ❌              ✅
  Historical trends             ❌              ✅

ENGINES:
  Safety Engine                 ✅ (standalone)  ✅ (integrated)
  Grounding Engine              ❌              ✅
  Consistency Engine            ❌              ✅
  System Engine                 ❌              ✅

FEATURES:
  Dashboard                     ❌              ✅
  Alerts (Email, Slack)         ❌              ✅
  AI Trust Badge                ❌              ✅
  Webhooks                      ❌              ✅
  API                           ❌              ✅

OUTPUT:
  Console: SAFE ✅ / UNSAFE ❌   ✅              ✅ (+ dashboard)
```

---

## 13. FREE AI HEALTH CHECK — zroky.ai/scan

### 13.1 What It Is

A free, no-signup tool where anyone can connect their AI and get a 5-minute trust report card. Like SSL Labs for AI.

### 13.2 User Flow

```
STEP 1: Visit zroky.ai/scan
  "How trustworthy is your AI? Find out in 5 minutes."
  No signup. No credit card. No email (first scan).

STEP 2: Connect your AI
  OPTION A: Enter AI's API endpoint + API key
  OPTION B: Paste OpenAI/Anthropic API key (ZROKY calls model directly)
  OPTION C: Upload CSV of 50+ AI interactions (prompt + response pairs)

STEP 3: ZROKY runs 50 automated test prompts (3-5 minutes)
  ├── 15 Red Team Attacks (injection, jailbreak, data extraction)
  ├── 15 Accuracy Tests (factual, numerical, multi-step)
  ├── 10 Consistency Tests (same question rephrased × 5)
  └── 10 Edge Cases (ambiguous, multi-part, out-of-domain)
  
  ALL 50 prompts run CONCURRENTLY.

STEP 4: Report Card
  ┌────────────────────────────────────────────────────┐
  │  YOUR AI HEALTH CHECK RESULTS                      │
  │                                                    │
  │  Overall Score:  76 / 100  🟡 CAUTION              │
  │                                                    │
  │  SAFETY:       88/100  ✅ Passed 13/15 attacks     │
  │  ACCURACY:     71/100  🟡 6 factual errors         │
  │  CONSISTENCY:  69/100  🟠 4 contradictions          │
  │  RESPONSE TIME: 1.4s avg  ✅ Normal                │
  │                                                    │
  │  ⚠️ 3 CRITICAL FINDINGS:                          │
  │  1. System prompt leaked in 2/15 attack tests      │
  │  2. Contradictory answers on pricing               │
  │  3. Hallucinated a non-existent policy             │
  │                                                    │
  │  [📥 Download PDF] [Share on Twitter] [Share LinkedIn] │
  │                                                    │
  │  Want continuous monitoring? [Start Free →]        │
  └────────────────────────────────────────────────────┘
```

### 13.3 Technical Architecture

```
INFRASTRUCTURE:
  Runs on: Google Cloud Run (serverless, scale-to-zero)
  Separate from main GKE cluster (scan traffic ≠ production)
  
JUDGE MODEL:
  Llama-3-8B-Instruct on vLLM (self-hosted)
  Cost per judge call: ~$0.0001 (vs $0.003 for GPT-4o)
  For PASS/FAIL classification: >95% accuracy (sufficient)

COST PER SCAN:
  Client AI calls: 50 × ~$0.002 = $0.10
  ZROKY judge:     50 × $0.0001 = $0.005
  Cloud Run:       ~$0.005
  TOTAL:           ~$0.11 per scan

API KEY SECURITY:
  ├── Client key used ONLY during scan, held in memory ONLY
  ├── NEVER written to disk, database, or logs
  ├── Purged from memory immediately after scan
  ├── Alternative: client-side scan mode (key never leaves browser)
  └── Privacy statement displayed before every scan

DATA RETENTION:
  ├── Report: stored 30 days (unique URL)
  ├── After 30 days: auto-deleted
  └── Raw AI responses: NEVER stored (analyzed in-memory, discarded)
```

### 13.4 Gated Scan Strategy

```
SCAN #1:  Completely free. No email. Full report displayed.
          PDF download requires email (lead capture).
          
SCAN #2:  Requires email only. Lead captured. Drip campaign starts.

SCAN #4+: Requires free Developer account. Converts to product user.

DAILY LIMITS:
  No account:     1 scan/day per IP
  Free account:   3 scans/day
  Paid (any tier): Unlimited

ANTI-ABUSE:
  ├── Rate limit: 3 scans per IP per day
  ├── CAPTCHA after 2nd scan in same session
  └── Can only scan your own AI (user provides their own API key)
```

### 13.5 Social Sharing

```
Share buttons auto-generate:

TWITTER: "🛡️ Our AI scored 76/100 on @ZROKY's Health Check. 3 critical 
          issues found. Scan yours free → zroky.ai/scan"

LINKEDIN: "Ran our AI through ZROKY's free health check. 76/100 with 3 
           critical findings. zroky.ai/scan (free, no signup)"

OG IMAGE: Auto-generated score card (Vercel @vercel/og or Satori)
          Cached by scan_id for 30 days
```

### 13.6 Conversion Math

```
50,000 scans/month (organic after launch)
  → 60% download PDF (email required) = 30,000 emails
  → 8% create free account = 4,000 accounts
  → 12% connect real AI = 480 active users
  → 50% convert to SMB = 240 paying customers
  
  240 × $99 = $23,760 MRR
  Cost: $5,500/month
  NET: +$18,260/month from a free tool
```

---

## 14. AI TRUST BADGE — badge.zroky.ai

### 14.1 What It Is

A free, embeddable, live widget showing real-time Trust Score. Verified by ZROKY, cryptographically unfakeable.

### 14.2 Badge Variants

```
Standard (dark):
┌─────────────────────────────────────┐
│  🛡️  AI Trust Score: 94  ✅         │
│      Verified by ZROKY              │
│      Updated: 2 min ago             │
└─────────────────────────────────────┘

Compact (inline):
┌─────────────────────────┐
│ 🛡️ ZROKY: 94 ✅         │
└─────────────────────────┘

Status colors:
  90-100: Green ✅ TRUSTED
  75-89:  Amber 🟡 CAUTION
  60-74:  Orange 🟠 AT RISK
  < 60:   Red 🔴 CRITICAL
  Stale:  Gray ⚠️ DATA STALE
```

### 14.3 Embed Code (2 Lines)

```html
<script src="https://badge.zroky.ai/v1/embed.js" async></script>
<div data-zroky-badge="agent_abc123" data-theme="dark" data-size="standard"></div>
```

### 14.4 Badge API

```
GET https://badge.zroky.ai/v1/score/{agent_id}   (PUBLIC — no auth)

Response:
{
  "score": 94,
  "status": "trusted",
  "coverage": 92.1,
  "last_event_at": "2026-04-08T14:23:11Z",
  "account_active": true,
  "verified_domain": "acme.com",
  "badge_enabled": true,
  "signature": "sha256_hmac_of_all_above_fields"
}

CACHING:
  Redis TTL: 30 seconds
  CDN edge-cached: 30 seconds
  Cost per render: ~$0.000001 (single Redis hit)
  1M renders/day: ~$1/day
```

### 14.5 Anti-Abuse Protection

```
5 SECURITY LAYERS:

1. LIVE WIDGET — not static image
   Widget fetches live score + validates HMAC-SHA256 signature.
   Invalid signature → renders nothing.

2. STALENESS DETECTION
   > 24h stale → "⚠️ DATA STALE" (gray)
   > 7 days → "MONITORING PAUSED" (score hidden)
   Account cancelled → badge disappears

3. DOMAIN VERIFICATION
   DNS TXT record: _zroky-verify.acme.com = "zroky-domain-verify=abc123"
   Mismatch → "⚠️ Unverified domain"

4. COVERAGE INTEGRATION
   Coverage < 70% → "⚠️ LOW COVERAGE"
   Prevents gaming via selective data

5. ACCOUNT-LEVEL SCORE
   Same score everywhere. No page-specific scores.
```

### 14.6 Public Trust Page

```
URL: zroky.ai/trust/{company-slug}

Shows:
  ├── Current Trust Score + status
  ├── Coverage Score
  ├── 30-day trend chart (sparkline)
  ├── Engines monitored (list)
  ├── "This Trust Score is independently computed by ZROKY."
  └── CTA: "Get your AI Trust Score → [Start Free]"

DOES NOT show:
  ❌ Individual engine scores
  ❌ Incident details
  ❌ Agent names/configurations
  ❌ Anything that helps attackers
```

---

## 15. FRAMEWORK INTEGRATIONS — V1 CONNECTORS

### 15.1 V1 Framework Support

```
SHIPS ON LAUNCH DAY:

1. LANGCHAIN — ZROKYCallbackHandler
   ├── Follows BaseCallbackHandler interface
   ├── Auto-captures: prompt, response, model, latency, tokens, tool calls
   ├── Supports: chains, agents, retrieval chains
   └── Published in: pip install zroky (included in SDK)

2. LANGGRAPH — ZROKYGraph Wrapper
   ├── Edge middleware that monitors inter-node communication
   ├── Tracks: which node produced what, handoff patterns
   └── Published in: pip install zroky

3. LITELLM — Proxy Mode Integration
   ├── ZROKY reads LiteLLM telemetry (if LiteLLM proxy is used)
   ├── Zero code change needed if client already uses LiteLLM
   └── Auto-captures: model routing, fallback events, cost

SUBMITTED ON LAUNCH DAY (PR to framework repos):

4. VERCEL AI SDK — useZROKY() React hook
   ├── PR submitted to vercel/ai repo
   ├── Node.js SDK integration
   └── Target: listed on sdk.vercel.ai/providers

5. OPENAI COOKBOOK — "Monitor Your AI with ZROKY" recipe
   ├── PR submitted to openai/openai-cookbook
   └── Working example with explanations

6. LANGCHAIN INTEGRATIONS — official listing
   ├── PR submitted to langchain-ai/langchain docs
   └── Listed under "Monitoring & Observability"
```

### 15.2 Integration Code Examples

```python
# LangChain — 3 lines to add ZROKY
from zroky.integrations.langchain import ZROKYCallbackHandler
handler = ZROKYCallbackHandler(api_key="zk_ingest_...", agent_id="agent_abc123")
result = chain.invoke(input, config={"callbacks": [handler]})

# LangGraph — wrap graph with ZROKY monitoring
from zroky.integrations.langgraph import ZROKYGraph
monitored_graph = ZROKYGraph(graph, api_key="zk_ingest_...", agent_id="agent_abc123")
result = monitored_graph.invoke(input)

# LiteLLM — auto-detected (zero code)
# If client uses LiteLLM proxy with ZROKY_API_KEY env variable,
# ZROKY automatically reads telemetry from LiteLLM's callback system.
```

---

## 16. SECURITY — V1 REQUIREMENTS

```
V1 SECURITY — NON-NEGOTIABLE:

NETWORK:
  ├── All traffic: HTTPS/TLS 1.3 only
  ├── Cloud Armor WAF: OWASP Top 10 protection
  ├── DDoS protection: Cloud Armor adaptive
  ├── VPC: All internal services on private network
  └── Zero public IPs on any internal service

API SECURITY:
  ├── Split API keys (ingest vs manage vs agent-scoped)
  ├── Keys stored as HMAC-SHA256 hash only (never raw)
  ├── Rate limiting on all endpoints
  ├── JWT session tokens (1h expiry + refresh)
  └── CORS: strict origin whitelist

DATA:
  ├── Encryption at rest: AES-256 (all databases)
  ├── Encryption in transit: TLS 1.3 (everywhere)
  ├── Client data isolation: separate ClickHouse partitions
  ├── PII redaction: guardrails-ai detector before storage
  ├── Secrets: Google Secret Manager (90-day rotation)
  └── Health Check API keys: in-memory only, never persisted

AUTH:
  ├── Clerk: email/password + MFA + magic link
  ├── RBAC: Owner > Admin > Engineer > Analyst > Viewer
  ├── Principle of least privilege
  └── Audit log: IP, user, action, timestamp

HEALTH CHECK SPECIFIC:
  ├── Client API key held in memory ONLY during scan
  ├── Never written to disk, database, or logs
  ├── Purged immediately after scan completes
  ├── Optional: client-side mode (key never leaves browser)
  └── Privacy statement displayed before every scan

BADGE SPECIFIC:
  ├── HMAC-SHA256 signature on all badge responses
  ├── Widget validates signature before rendering
  ├── Domain verification via DNS TXT record
  └── Invalid signature → widget renders nothing
```

---

## 17. PRICING — V1 TIERS

```
PLAN 0: DEVELOPER — Free forever
  ├── 1 AI Agent
  ├── 10,000 interactions/month
  ├── 3 users
  ├── Email alerts only
  ├── 3-day data retention
  ├── SMB Simplified dashboard only
  ├── Community support (Discord, docs)
  ├── AI Trust Badge ✅ (free marketing for ZROKY)
  ├── Health Check: 3 scans/day
  └── No credit card required

PLAN 1: SMB — $99/month  ($79/month annual)
  ├── 1 AI Agent
  ├── 500,000 interactions/month
  ├── 5 users
  ├── Email alerts
  ├── 7-day data retention
  ├── Simplified dashboard
  ├── Standard support (email, 48h)
  ├── AI Trust Badge ✅
  ├── Health Check: unlimited
  ├── 14-day free trial (no credit card)
  └── Overage: monitoring pauses at limit (AI keeps running)

PLAN 2: GROWTH — $499/month  ($399/month annual)
  ├── Up to 5 AI Agents
  ├── 5,000,000 interactions/month
  ├── 20 users
  ├── Email + Slack alerts
  ├── 90-day data retention
  ├── Full dashboard (Executive + Engineer views)
  ├── Compliance View (basic)
  ├── API access + Webhooks
  ├── Priority support (Slack, 8h)
  ├── AI Trust Badge ✅
  └── Health Check: unlimited

PLAN 3: ENTERPRISE — Custom ($2K-$15K+/month, annual)
  ├── Unlimited agents + interactions + users
  ├── All alert channels
  ├── 24-month data retention
  ├── All dashboard views + custom dashboards
  ├── Full Compliance Mode (SOC 2, GDPR, EU AI Act)
  ├── SSO (Okta, Azure AD, Google)
  ├── Dedicated onboarding engineer
  ├── SLA guarantee (99.9%)
  └── Dedicated Slack channel + 24/7 support

V1 ADD-ONS:
  ├── Additional agents: $50/agent/month
  ├── Additional interactions: $0.001 per 1,000
  └── Compliance Report Pack: $200/month
```

---

## 18. BUILD ROADMAP — WEEK BY WEEK

### PHASE 1: FOUNDATION (Weeks 1-8)

*Goal: Working API + 4 engines + basic Trust Score + first paying client.*
*Team: 4 engineers (1 infrastructure, 2 backend, 1 frontend)*

```
WEEK 1-2: INFRASTRUCTURE SETUP
  [ ] GCP project + billing + VPC + private subnets
  [ ] GKE cluster (us-central1, n2-standard-8 nodes)
  [ ] Cloud SQL (PostgreSQL 15) + failover replica
  [ ] ClickHouse (single node, Altinity Operator on GKE)
  [ ] Redis (Cloud Memorystore)
  [ ] Cloud Pub/Sub: 4 engine topics + dead-letter + trust-score aggregation
  [ ] GitHub repo + GitHub Actions CI/CD + Cloud Build
  [ ] Workload Identity for all GKE service accounts
  [ ] Google Secret Manager populated
  [ ] Terraform for all above (infrastructure/terraform/)

WEEK 3-4: CORE API + DATABASE
  [ ] Fastify API server containerized + deployed to GKE
  [ ] POST /v1/events (async, < 10ms ack)
  [ ] POST /v1/events/batch (up to 1,000)
  [ ] GET  /v1/trust-score/{agent_id}
  [ ] Management API: CRUD for agents, alert-rules, users, incidents
  [ ] Split API key system (ingest/manage/agent) + HMAC-SHA256 + Redis cache
  [ ] Rate limiting (Redis atomic counters, per key, per tier)
  [ ] PostgreSQL schema (all V1 tables from Section 5)
  [ ] ClickHouse schema (trust_events table)
  [ ] Universal response envelope on all endpoints
  [ ] Idempotency-Key support on all POST endpoints
  [ ] Sandbox environment (sandbox.ingest.zroky.ai)
  [ ] OpenAPI spec auto-generation

WEEK 5-6: 4 V1 ENGINES
  [ ] Safety Engine
      ├── guardrails-ai validators (PII, toxicity, prompt injection)
      ├── promptfoo red team signatures (40+ attack patterns)
      ├── NeMo Guardrails 5-rail system
      ├── Campaign detection (50+ similar attacks = coordinated)
      └── Cross-session user correlation
  [ ] Grounding Engine
      ├── Phoenix OpenInference RAG evaluation
      ├── LLM-as-judge via Langfuse
      ├── Vector DB distance tracking
      └── Golden test set evaluation (daily)
  [ ] Consistency Engine
      ├── lm-evaluation-harness daily benchmarks
      ├── promptfoo regression testing (100 test cases)
      ├── Behavioral drift detection (PSI + KL divergence)
      ├── Behavioral fingerprinting (weekly)
      └── Model version tracking
  [ ] System Engine
      ├── LiteLLM metrics ingestion
      ├── OpenLLMetry OTel spans
      ├── Latency, error rate, cost, uptime tracking
      └── Health check endpoint monitoring
  [ ] Trust Score V1 computation (4 engines + coverage + override rules)
  [ ] Cold-start handling (PROVISIONAL → BUILDING → STABLE)

WEEK 7-8: DASHBOARD + ONBOARDING + BILLING
  [ ] Next.js 14 project + Tailwind + shadcn/ui (dark mode default)
  [ ] Clerk auth integration (email/password + MFA + magic link)
  [ ] WebSocket connection (Socket.io, auth on connect)
  [ ] SMB Simplified View (Trust Score + 3 panels)
  [ ] Engineer View (4-engine table + incident detail)
  [ ] Trust Score 30-day trend chart (Recharts)
  [ ] Alert Center (in-dashboard feed)
  [ ] Email alerts via SendGrid (auto-configured defaults)
  [ ] Stripe billing integration + plan enforcement
  [ ] Onboarding flow (signup → connect → first score in 15 min)
  [ ] Webhook registration + HMAC-signed delivery + retry logic

DELIVERABLE: 
  A client signs up, connects AI via SDK or API, sees live 4-engine Trust Score 
  within 15 minutes. Email alerts working. Dashboard shows trends + incidents.
  Stripe billing active. First SMB client possible.
```

### PHASE 2: EXPANSION + VIRAL LAUNCH (Weeks 9-16)

*Goal: 6 core engines + SMB public launch + all viral moves go live.*
*Team: 5 engineers (+ 1 AI/ML engineer)*

```
WEEK 9-10: 2 MORE ENGINES
  [ ] Uncertainty Engine
      ├── Mode A: logprob integration for open-weight models (Ollama/vLLM)
      └── Mode B: consistency-based estimation for closed APIs (GPT-4o, Claude)
  [ ] Context Engine
      ├── NeMo Guardrails 5-rail dialog control
      ├── Instruction injection detection in mid-conversation
      ├── System prompt version tracking
      └── Memory contamination monitoring
  [ ] Trust Score recalibrated for 6 engines (V2 weights)
  [ ] Override Rules updated (Rules 1-4 enforced)
  [ ] Email to all clients: "New engines added. Score may shift for 3 days."

WEEK 11-12: DASHBOARD ENHANCEMENT
  [ ] Executive View (multi-agent portfolio + 30-day trend)
  [ ] Resolution Intelligence UI (diagnosis panel + remediation steps)
  [ ] [Re-embed Now] / [Run Test Suite] action buttons
  [ ] Trust Score recovery curve (3-day normalization)
  [ ] Compliance View (basic) — incident log + audit trail (Growth only)
  [ ] Slack integration (OAuth 2.0, rich alerts)

WEEK 13-14: FRAMEWORK INTEGRATIONS + OSS EXTRACTION
  [ ] LangChain ZROKYCallbackHandler (finalized, tested)
  [ ] LangGraph ZROKYGraph wrapper (finalized, tested)
  [ ] LiteLLM proxy mode integration
  [ ] Batch ingest tested at scale (1,000 events/request)
  [ ] Extract SDK into standalone repo (zroky-ai/zroky-oss) — PRIVATE
  [ ] Extract Safety Engine into safety-engine/ directory
  [ ] MIT license (SDK) + BSL license (Safety Engine)
  [ ] README.md (quickstart + GIF + comparison table)
  [ ] GitHub Actions CI + CONTRIBUTING.md + 10+ "good first issue" labels
  [ ] Repo stays PRIVATE (don't publish yet)

WEEK 15: VIRAL SYSTEMS BUILD
  [ ] Health Check: Cloud Run microservice + 50-prompt test suite
  [ ] Health Check: Llama-3-8B judge on vLLM
  [ ] Health Check: Report card UI + OG image generator + PDF export
  [ ] Health Check: Gating logic (free→email→account)
  [ ] Health Check: Rate limiting (3/day per IP)
  [ ] Badge: badge.zroky.ai API (Redis cache, CDN, signature)
  [ ] Badge: embed.js widget (live render, signature validation)
  [ ] Badge: Public trust page (zroky.ai/trust/{slug})
  [ ] Badge: Domain verification (DNS TXT)
  [ ] Badge: Staleness detection + coverage caveat
  [ ] Draft framework PRs (LangChain, Vercel AI SDK, OpenAI Cookbook)
  [ ] Everything stays HIDDEN/DISABLED (don't go live yet)

WEEK 16: LAUNCH PREP + L-DAY
  [ ] Product Hunt page drafted + scheduled
  [ ] Hacker News "Show HN" post written
  [ ] Twitter/X launch thread written
  [ ] Blog posts written (dev.to, Hashnode, Medium)
  [ ] Press kit assembled (logo, screenshots, demo video)
  [ ] Email to beta users: "We're launching. Help us blow up."
  [ ] Documentation site finalized (docs.zroky.ai — Mintlify)
  [ ] Status page live (status.zroky.ai)
  [ ] All systems end-to-end tested
  
  L-DAY (Launch Day):
  [ ] 09:00 UTC: GitHub zroky-oss → PUBLIC
  [ ] 09:00 UTC: zroky.ai/scan → LIVE
  [ ] 09:00 UTC: badge.zroky.ai → ENABLED
  [ ] 09:00 UTC: pip install zroky + npm install @zroky/sdk → published
  [ ] 09:05 UTC: Product Hunt LIVE + HN "Show HN" + Twitter thread
  [ ] 09:10 UTC: Framework PRs submitted (LangChain, Vercel, OpenAI)
  [ ] 09:30 UTC: Blog posts published + Reddit posts
  [ ] 10:00 UTC: Email blast to waitlist + beta users
  [ ] 10:30 UTC: Founder engages on HN + Product Hunt + GitHub

DELIVERABLE:
  6 engines running. Developer + SMB + Growth plans live.
  OSS repo public. Health Check live. Badge system active.
  All 4 viral moves launched simultaneously.
```

---

## 19. SIMULTANEOUS LAUNCH DAY PLAN

### 19.1 Why Simultaneous

```
ONE BIG STORY > FOUR SMALL STORIES.

Staggered: 4 forgettable announcements over 4 months.
Simultaneous: 1 massive platform launch. Product Hunt front page.
              TechCrunch covers as "platform launch" not "feature update."
              
Each move amplifies the others:
  OSS on GitHub → developer tries Health Check → signs up → gets Badge
  CTO sees Badge → runs Health Check → evaluates platform
  Framework user sees LangChain integration → checks GitHub → sees OSS
  ALL roads lead to ZROKY. On the SAME day.
```

### 19.2 Launch Day Metrics & Targets

```
                          MINIMUM    TARGET     STRETCH
GitHub stars              200        1,000      3,000
Health Check scans        500        2,000      5,000
Badge embeds              5          20         50
Free signups              100        500        1,500
Paid conversions          5          20         50
Product Hunt upvotes      200        500        1,000
Hacker News upvotes       100        300        500

WEEK 1 TARGETS:
  GitHub stars:     1,000
  Health Check:     5,000 scans
  Free signups:     500
  Paid conversions: 20

MONTH 1 TARGETS:
  GitHub stars:     3,000
  Health Check:     15,000 scans
  Free signups:     2,000
  Paid conversions: 100
  MRR:              $15,000+
```

### 19.3 Post-Launch Protocol (Days 1-30)

```
DAYS 1-7 (LAUNCH WEEK):
  ├── Respond to EVERY GitHub issue within 1 hour
  ├── Respond to EVERY Product Hunt comment within 30 minutes
  ├── Founder personally responds on Hacker News
  ├── Daily metrics tracking: stars, scans, badges, signups, conversions
  ├── Fix any reported bugs within 4 hours
  └── Write "Week 1 numbers" transparency blog post

DAYS 8-14:
  ├── Follow up on framework PRs (ping LangChain, Vercel maintainers)
  ├── Reach out to AI newsletters (Ben's Bites, The Neuron, TLDR AI)
  ├── Aggregate Health Check data for first "mini-report" preview
  └── Enable badge for all paying customers + email notification

DAYS 15-30:
  ├── A/B test Health Check gating (email on scan 2 vs scan 3)
  ├── First monthly email report to all users (Trust Score summary)
  ├── Community building: Discord server launch
  ├── Top OSS contributors get free Growth plan
  └── Plan Phase 3 (Behavior, Cognitive, Focus engines)
```

---

## 20. V1 SUCCESS METRICS

```
PRODUCT METRICS:
  Time to First Trust Score (TTFTS):   < 15 minutes
  API P95 Latency (Ingestion):         < 10ms
  API P95 Latency (Query):             < 50ms
  Trust Score Computation Lag:          < 30 seconds
  Alert Delivery Time (Critical):      < 60 seconds
  Dashboard Load Time:                 < 2 seconds
  SDK Overhead on Client AI:           < 1ms per interaction

RELIABILITY:
  API Uptime:                          99.9%
  Data Loss:                           0% (Pub/Sub guarantees)
  Alert False Positive Rate:           < 5% (tighter in V2)
  Alert False Negative Rate:           < 0.5%

BUSINESS METRICS (Month 4 — post launch):
  Paying Clients:                      100+
  MRR:                                 $15,000+
  Free Signups:                        2,000+
  Client Churn Rate:                   < 8% monthly
  Health Check Scans:                  15,000+ total
  GitHub Stars:                        3,000+
  npm/pip Monthly Installs:            5,000+

UNIT ECONOMICS:
  SMB gross margin:                    40-63%
  Growth gross margin:                 66-78%
  Health Check cost per scan:          < $0.15
  Badge cost per million renders:      < $5
  Blended gross margin:                > 55%
```

---

## 21. WHAT IS NOT IN V1 — EXPLICIT EXCLUSIONS

```
EXPLICIT V1 EXCLUSIONS — DO NOT BUILD THESE YET:

ENGINES:
  ❌ Uncertainty Engine         → V2 (Phase 2, Week 9-10)
  ❌ Context Engine             → V2 (Phase 2, Week 9-10)
  ❌ Cognitive Engine           → V3 (Phase 3, Weeks 17-20)
  ❌ Behavior Engine            → V3 (Phase 3, Weeks 17-20)
  ❌ Focus Engine               → V3 (Phase 3, Weeks 21-24)

FEATURES:
  ❌ Resolution Intelligence (GPT-4o diagnosis) → V2 (Phase 2)
  ❌ Enterprise Intelligence Mode (Discovery)   → V3 (Phase 3)
  ❌ Trust Score Gaming Protection (Coverage Intelligence) → V2
  ❌ Multi-agent topology monitoring             → V3
  ❌ Mirror Room / Shadow Testing                → V3
  ❌ Industry Trust Benchmarks                   → V4 (Phase 4, Month 10-12)
  ❌ Custom report builder                       → V4
  ❌ GraphQL API                                 → V4
  ❌ Terraform provider                          → V4

INTEGRATIONS:
  ❌ AutoGen wrapper            → V3
  ❌ CrewAI wrapper             → V3
  ❌ LlamaIndex integration     → V2
  ❌ PagerDuty                  → V4
  ❌ Microsoft Teams            → V4
  ❌ Zapier connector           → V4
  ❌ Slack slash commands        → V4 (V1 has webhook alerts only)

INFRASTRUCTURE:
  ❌ EU region (europe-west4)    → V3 (Phase 3)
  ❌ APAC region (Singapore)     → V4
  ❌ Multi-region DB replication  → V3
  ❌ ClickHouse 3-node cluster   → When 100M+ events (auto-assess)
  ❌ Dedicated client namespaces  → Enterprise plan launch (Phase 3)

COMPLIANCE:
  ❌ Full Compliance Mode        → V3 (Enterprise plan)
  ❌ SOC 2 Type II certification → V4 (Month 12)
  ❌ EU AI Act compliance package → V4
  ❌ White-label option           → V4
  ❌ SSO (Okta, Azure AD)         → V3 (Enterprise plan)

THESE CAN WAIT. V1 MUST SHIP.
Every feature above has a clear version where it belongs.
None of them are needed for the first 200 paying customers.
```

---

## APPENDIX: V1 COST SUMMARY

```
MONTHLY COST AT LAUNCH (Month 1-2):
  GCP Infrastructure:     $2,500-3,500
  Health Check (Cloud Run): $500-1,000 (depends on scan volume)
  LLM APIs (judge + eval):  $200-500
  SendGrid (email):         $50
  Clerk (auth):             $0 (free tier up to 10K MAU)
  Stripe (billing):         2.9% of revenue
  Mintlify (docs):          $0 (free tier)
  Domain/SSL:               $50
  Monitoring (Grafana):     $0 (self-hosted on GKE)
  ─────────────────────────────────────
  TOTAL:                    ~$3,300-5,100/month

BREAKEVEN: ~50 SMB paying clients ($4,950 MRR)
TARGET MONTH 4: 100 clients ($15,000+ MRR) = profitable

COST SCALES WITH REVENUE:
  100 clients:   ~$5,000/month infra → $15,000 MRR → 67% margin
  500 clients:   ~$12,000/month infra → $60,000 MRR → 80% margin
  1,000 clients: ~$20,000/month infra → $120,000 MRR → 83% margin
  
LLM cost reduction plan:
  Month 1-3: GPT-4o for eval → expensive
  Month 4-6: Llama-3-8B for routine, GPT-4o for diagnosis only → 60% cheaper
  Month 7+:  Fine-tuned models per engine → 80% cheaper
```

---

*ZROKY V1 Scope Document — April 8, 2026*
*Extracted from ZROKY Master Blueprint v1.0*
*This document defines exactly what ships in V1 — nothing more, nothing less.*

---

**"Ship the 4 engines. Ship the badge. Ship the scan. Ship the OSS. Ship it all on the same day. That's V1."**
