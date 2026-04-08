# Architecture Research — ZROKY AI Trust Infrastructure

**Researched:** 2026-04-09 | **Source:** V1 Scope Document

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ZROKY V1 ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  CLIENTS                    ZROKY PLATFORM                        │
│  ┌──────┐                  ┌────────────────────────────────┐    │
│  │Python│──┐               │  ┌──────────┐   ┌──────────┐  │    │
│  │ SDK  │  │   HTTPS/TLS   │  │ Fastify  │   │  Kong    │  │    │
│  └──────┘  ├──────────────►│  │ API      │◄──│ Gateway  │  │    │
│  ┌──────┐  │               │  │ Server   │   │ (V2)     │  │    │
│  │Node  │──┤               │  └────┬─────┘   └──────────┘  │    │
│  │ SDK  │  │               │       │                         │    │
│  └──────┘  │               │  ┌────▼─────┐                  │    │
│  ┌──────┐  │               │  │ Cloud    │                  │    │
│  │ Go   │──┘               │  │ Pub/Sub  │                  │    │
│  │ SDK  │                  │  │ (4 topics)│                  │    │
│  └──────┘                  │  └────┬─────┘                  │    │
│                            │       │                         │    │
│  INTEGRATIONS              │  ┌────▼──────────────────────┐ │    │
│  ┌──────────┐              │  │   ENGINE WORKERS (FastAPI)  │ │    │
│  │LangChain │              │  │  ┌────────┐ ┌──────────┐  │ │    │
│  │LangGraph │              │  │  │Safety  │ │Grounding │  │ │    │
│  │LiteLLM   │              │  │  │Engine  │ │Engine    │  │ │    │
│  └──────────┘              │  │  └────────┘ └──────────┘  │ │    │
│                            │  │  ┌──────────┐ ┌────────┐  │ │    │
│  DASHBOARD                 │  │  │Consistency│ │System  │  │ │    │
│  ┌──────────┐              │  │  │Engine    │ │Engine  │  │ │    │
│  │ Next.js  │◄─WebSocket──│  │  └──────────┘ └────────┘  │ │    │
│  │ 14       │              │  └───────────────┬───────────┘ │    │
│  └──────────┘              │                  │              │    │
│                            │  ┌───────────────▼───────────┐ │    │
│                            │  │    TRUST SCORE COMPUTER     │ │    │
│                            │  │  (aggregates 4 engines +    │ │    │
│                            │  │   coverage + overrides)     │ │    │
│                            │  └───────────────┬───────────┘ │    │
│                            │                  │              │    │
│                            │  ┌───────────────▼───────────┐ │    │
│                            │  │         DATA LAYER          │ │    │
│                            │  │  PostgreSQL │ ClickHouse   │ │    │
│                            │  │  Redis      │ BigQuery     │ │    │
│                            │  └─────────────────────────── │ │    │
│                            └────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Component Boundaries

### 1. API Gateway Layer
- **Fastify server** receives all HTTP requests
- Validates API keys (HMAC-SHA256 lookup in Redis cache → PostgreSQL fallback)
- Rate limiting via Redis atomic counters
- Routes to appropriate handler
- Returns universal response envelope

### 2. Event Ingestion Pipeline
- POST /events → validate payload → publish to Cloud Pub/Sub
- 4 Pub/Sub topics: `safety-events`, `grounding-events`, `consistency-events`, `system-events`
- Each event goes to ALL 4 topics (fan-out pattern)
- Each engine subscribes to its topic independently

### 3. Engine Workers (Python/FastAPI Microservices)
- Each engine = 1 independently deployable FastAPI service
- Each subscribes to its Pub/Sub topic
- Processes event through its analysis pipeline
- Writes engine_score to ClickHouse `trust_events` table
- Publishes score update to Redis (for real-time dashboard)

### 4. Trust Score Computer
- Triggered after ALL 4 engines produce scores for an event
- Reads latest scores from ClickHouse (time-window aggregation)
- Applies formula: 0.30×Safety + 0.25×Grounding + 0.20×Consistency + 0.10×System + 0.15×Coverage
- Applies override rules (safety floor, grounding crash, etc.)
- Writes computed Trust Score to Redis (real-time) + ClickHouse (persistent)

### 5. Dashboard (Next.js 14)
- Server-rendered pages (SSR for initial load)
- WebSocket connection for real-time Trust Score updates
- 3 views: SMB (simple), Engineer (detail), Executive (portfolio)
- Reads from Fastify API (which reads from Redis cache / ClickHouse)

### 6. Alert System
- Triggered by Trust Score changes or engine events
- Email via SendGrid, Slack via webhooks
- Webhook delivery to client endpoints (HMAC-signed)

### 7. Public Services
- Health Check: standalone FastAPI service (Llama-3-8B judge on Cloud Run)
- Badge: Redis-cached score → CDN-cached widget embed
- Trust Page: SSR Next.js page at zroky.ai/trust/{slug}

## Data Flow

```
1. Client SDK sends event
        │
        ▼
2. Fastify validates + publishes to Pub/Sub (all 4 topics)
        │
        ├──► Safety Engine analyzes → writes safety_score to ClickHouse
        ├──► Grounding Engine analyzes → writes grounding_score to ClickHouse
        ├──► Consistency Engine analyzes → writes consistency_score to ClickHouse
        └──► System Engine analyzes → writes system_score to ClickHouse
                │
                ▼
3. Trust Score Computer aggregates → applies formula + overrides
        │
        ├──► Writes Trust Score to Redis (real-time cache)
        ├──► Writes Trust Score to ClickHouse (persistent analytics)
        ├──► Pushes to WebSocket (dashboard update)
        └──► Triggers alerts if thresholds crossed
```

## Database Responsibility Split

| Database | What it stores | Access pattern |
|----------|---------------|----------------|
| **PostgreSQL** | Clients, agents, API keys, subscriptions, incidents, alert rules, webhook configs | CRUD, transactional, low-volume |
| **ClickHouse** | trust_events (billions of rows), engine scores, Trust Score history | Append-only, analytical queries, time-window aggregations |
| **Redis** | Current Trust Score (cache), rate limit counters, sessions, real-time scores | Key-value, sub-ms reads, atomic counters |
| **BigQuery** | Monthly aggregations, cross-client analytics, ad-hoc reporting | Batch queries, long-term retention |

## Suggested Build Order (Dependencies)

```
PHASE 1: Foundation (no business logic)
  ├── Terraform infra (GKE, Cloud SQL, Memorystore, Pub/Sub)
  ├── PostgreSQL schema (clients, agents, api_keys)
  ├── ClickHouse schema (trust_events)
  ├── Redis key structure
  └── CI/CD pipeline

PHASE 2: API + Auth (the front door)
  ├── Fastify server setup
  ├── Clerk auth integration
  ├── API key management (generate, validate, revoke)
  ├── Event ingestion endpoint (POST /events)
  ├── Rate limiting middleware
  └── Universal response envelope

PHASE 3: Engines (the brain)
  ├── Safety Engine worker (most complex, highest priority)
  ├── Grounding Engine worker
  ├── Consistency Engine worker
  ├── System Engine worker
  └── Trust Score Computer

PHASE 4: Dashboard (the face)
  ├── Next.js project scaffold
  ├── Auth integration (Clerk)
  ├── SMB view → Engineer view → Executive view
  ├── WebSocket real-time updates
  └── Alert system (email + Slack)

PHASE 5: SDK + Onboarding (the handshake)
  ├── Python SDK
  ├── Node.js SDK
  ├── Go SDK (stub)
  ├── Onboarding flow
  └── Integration connectors (LangChain, LangGraph, LiteLLM)

PHASE 6: Billing + Viral (the revenue + growth)
  ├── Stripe integration
  ├── Tier enforcement
  ├── Health Check service
  ├── Badge service
  ├── OSS extraction
  └── Documentation site

PHASE 7: Launch prep
  ├── End-to-end testing
  ├── Security hardening
  ├── Performance optimization
  └── Launch day execution
```

## Scaling Considerations (V1 → V2)

| Component | V1 Scale | V2 Scale Need |
|-----------|----------|---------------|
| Engine workers | 1 replica each | Auto-scale per engine based on queue depth |
| ClickHouse | Single node (Altinity) | Sharded cluster |
| Redis | Single instance | Redis Cluster |
| Pub/Sub | Default quotas | Custom quotas for high-volume clients |
| API | Single region | Multi-region with global load balancer |

---
*Generated: 2026-04-09*
