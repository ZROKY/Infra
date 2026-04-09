# ZROKY — AI Trust Infrastructure

> Monitor, score, and certify AI agent behavior in production.

ZROKY provides a **unified Trust Score (0-100)** computed from 4 specialized engines (Safety, Grounding, Consistency, System) with real-time dashboards, alerts, SDKs, and an embeddable Trust Badge.

## Architecture

```
apps/
  web/                    → Next.js 14 dashboard
  docs/                   → Documentation site
services/
  api/                    → Fastify API server
  engine-safety/          → Safety Engine (Python/FastAPI)
  engine-grounding/       → Grounding Engine (Python/FastAPI)
  engine-consistency/     → Consistency Engine (Python/FastAPI)
  engine-system/          → System Engine (Python/FastAPI)
  trust-computer/         → Trust Score aggregation
  health-check/           → Free AI Health Check
packages/
  shared-types/           → Shared TypeScript types
  eslint-config/          → Shared ESLint config
  tsconfig/               → Shared TypeScript config
  sdk-python/             → Python SDK
  sdk-node/               → Node.js SDK
  sdk-go/                 → Go SDK
infra/
  terraform/              → GCP infrastructure as code
  k8s/                    → Kubernetes manifests
  docker/                 → Dockerfiles
```

## Quick Start

```bash
# Prerequisites: Node.js 20+, pnpm 9+, Python 3.11+, Docker
pnpm install
cp .env.example .env
docker compose up -d
pnpm dev
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Dashboard | Next.js 14, Tailwind CSS, shadcn/ui, Recharts |
| API | Fastify, TypeScript |
| Engines | Python 3.11, FastAPI, uvicorn |
| Databases | PostgreSQL 15, ClickHouse, Redis |
| Queue | Google Cloud Pub/Sub |
| Infrastructure | GCP/GKE, Terraform |
| CI/CD | GitHub Actions, Cloud Build |
| Auth | Clerk |
| Billing | Stripe |

## Development

```bash
pnpm dev          # Start all services
pnpm lint         # Lint all packages
pnpm test         # Run all tests
pnpm typecheck    # TypeScript type checking
pnpm build        # Build all packages
```

## License

Proprietary. All rights reserved.
