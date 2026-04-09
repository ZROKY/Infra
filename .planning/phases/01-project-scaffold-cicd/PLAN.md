# Phase 1 — Project Scaffold + CI/CD

**Goal:** Enterprise-grade monorepo structure, linting, formatting, CI/CD pipeline — zero business logic
**Requirements:** INFRA-07 (partial)
**Success criteria:** `pnpm install` works, `pnpm lint` passes, `pnpm test` passes, GitHub Actions green

---

## Plan 1: Monorepo Root + Package Manager Setup
**Wave:** 1 (no dependencies)
**Files to create/modify:**
- `package.json` (root — pnpm workspace)
- `pnpm-workspace.yaml`
- `.npmrc`
- `.nvmrc`
- `.gitignore`
- `turbo.json`
- `README.md`

**Tasks:**
1. Initialize root `package.json` with `"private": true`, project metadata
2. Create `pnpm-workspace.yaml` defining workspace packages: `apps/*`, `packages/*`, `services/*`, `infra/*`
3. Create `.npmrc` with `shamefully-hoist=true`, `strict-peer-dependencies=false`
4. Create `.nvmrc` with `20.11.0` (Node.js LTS)
5. Create `.gitignore` (node_modules, dist, .env, .turbo, coverage, terraform state)
6. Create `turbo.json` with pipeline: build, lint, test, typecheck
7. Create `README.md` with project overview + quickstart

**Verification:** `pnpm install` runs without errors from root

---

## Plan 2: Application + Service Scaffolds (Empty)
**Wave:** 2 (depends on Plan 1)
**Directories to create:**

```
apps/
  web/                    # Next.js 14 dashboard
  docs/                   # Documentation site (Mintlify)
services/
  api/                    # Fastify API server (Node.js)
  engine-safety/          # Safety Engine (Python/FastAPI)
  engine-grounding/       # Grounding Engine (Python/FastAPI)
  engine-consistency/     # Consistency Engine (Python/FastAPI)
  engine-system/          # System Engine (Python/FastAPI)
  trust-computer/         # Trust Score Computer (Python/FastAPI)
  health-check/           # Free Health Check service (Python/FastAPI)
packages/
  shared-types/           # TypeScript type definitions shared across apps
  eslint-config/          # Shared ESLint config
  tsconfig/               # Shared TypeScript config
  sdk-python/             # Python SDK (pip install zroky)
  sdk-node/               # Node.js SDK (@zroky/sdk)
  sdk-go/                 # Go SDK stub
infra/
  terraform/              # Terraform IaC
  k8s/                    # Kubernetes manifests
  docker/                 # Dockerfiles
scripts/                  # Dev scripts (setup, seed, migrate)
```

**Tasks:**
1. Create all directories with placeholder `package.json` (Node apps/packages) or `pyproject.toml` (Python services)
2. Each app/service gets a minimal `README.md` with purpose description
3. Python services: create `pyproject.toml` with project name, Python 3.11+, empty deps
4. Node apps/packages: create `package.json` with workspace name, empty deps

**Verification:** `pnpm install` picks up all workspace packages, directory tree matches spec

---

## Plan 3: TypeScript + ESLint + Prettier Configuration
**Wave:** 2 (depends on Plan 1, parallel with Plan 2)
**Files to create:**

```
packages/tsconfig/
  base.json               # Strict TypeScript base config
  nextjs.json             # Next.js specific extends
  node.json               # Node.js/Fastify specific extends
  package.json
packages/eslint-config/
  base.js                 # Shared ESLint rules
  next.js                 # Next.js specific rules
  node.js                 # Node.js specific rules
  package.json
.prettierrc               # Root Prettier config
.prettierignore
.editorconfig             # Editor standardization
```

**Tasks:**
1. Create `packages/tsconfig/base.json` — strict mode, ES2022 target, module resolution bundler
2. Create `nextjs.json` extending base — jsx preserve, next plugin
3. Create `node.json` extending base — module commonjs, no jsx
4. Create `packages/eslint-config/base.js` — @typescript-eslint, import order, no unused vars
5. Create `next.js` — extends base + next/core-web-vitals
6. Create `node.js` — extends base + node-specific rules
7. Create root `.prettierrc` — 2 spaces, single quotes, trailing commas, 100 print width
8. Create `.editorconfig` — consistent across IDEs

**Verification:** `pnpm lint` passes on empty project, no config errors

---

## Plan 4: Next.js Dashboard Scaffold
**Wave:** 3 (depends on Plan 2 + Plan 3)
**Location:** `apps/web/`
**Files to create:**

```
apps/web/
  package.json
  next.config.js
  tsconfig.json           # extends packages/tsconfig/nextjs.json
  .eslintrc.js            # extends packages/eslint-config/next.js
  tailwind.config.ts
  postcss.config.js
  src/
    app/
      layout.tsx          # Root layout with providers
      page.tsx            # Landing/redirect to dashboard
      globals.css         # Tailwind imports + CSS vars
    lib/
      utils.ts            # cn() utility for tailwind-merge
    components/
      ui/                 # shadcn/ui components (empty, added later)
```

**Tasks:**
1. Create `package.json` with Next.js 14, React 18, Tailwind CSS deps
2. Create `next.config.js` with transpilePackages for workspace packages
3. Create `tsconfig.json` extending `@zroky/tsconfig/nextjs.json`
4. Create Tailwind config with ZROKY design tokens (colors, spacing)
5. Create minimal `layout.tsx` + `page.tsx` that renders "ZROKY Dashboard — Coming Soon"
6. Set up `cn()` utility (clsx + tailwind-merge)

**Verification:** `pnpm --filter web dev` starts Next.js on port 3000, page renders

---

## Plan 5: Fastify API Server Scaffold
**Wave:** 3 (depends on Plan 2 + Plan 3, parallel with Plan 4)
**Location:** `services/api/`
**Files to create:**

```
services/api/
  package.json
  tsconfig.json           # extends packages/tsconfig/node.json
  .eslintrc.js            # extends packages/eslint-config/node.js
  src/
    server.ts             # Fastify server setup + plugin registration
    app.ts                # Application factory (testable)
    config/
      index.ts            # Environment config (typed, validated)
    plugins/
      cors.ts             # CORS plugin
      swagger.ts          # Swagger/OpenAPI auto-gen
    routes/
      health.ts           # GET /health — returns { status: 'ok' }
    lib/
      envelope.ts         # Universal response envelope { success, data, error, meta }
  test/
    health.test.ts        # Health endpoint test
```

**Tasks:**
1. Create `package.json` with Fastify, @fastify/cors, @fastify/swagger deps
2. Create typed config loader (env vars with defaults)
3. Create Fastify app factory in `app.ts` (for testability)
4. Create `server.ts` that boots the app
5. Create universal response envelope utility
6. Create `/health` route returning `{ success: true, data: { status: 'ok' } }`
7. Create health endpoint test with `vitest`

**Verification:** `pnpm --filter api dev` starts on port 4000, `GET /health` returns 200

---

## Plan 6: Python Service Template
**Wave:** 3 (parallel with Plan 4 + Plan 5)
**Location:** `services/engine-safety/` (template copied to other engines)
**Files to create:**

```
services/engine-safety/
  pyproject.toml
  Makefile                # make install, make test, make lint, make run
  src/
    engine_safety/
      __init__.py
      main.py             # FastAPI app factory
      config.py           # Pydantic Settings
      routes/
        __init__.py
        health.py         # GET /health
  tests/
    __init__.py
    test_health.py
  .python-version         # 3.11
```

**Tasks:**
1. Create `pyproject.toml` with FastAPI, uvicorn, pydantic-settings, pytest, ruff
2. Create `Makefile` with standard targets (install, test, lint, format, run)
3. Create FastAPI app factory in `main.py`
4. Create Pydantic Settings config
5. Create `/health` endpoint
6. Create health test with pytest
7. Copy template to: engine-grounding, engine-consistency, engine-system, trust-computer, health-check (with names adjusted)

**Verification:** `make install && make test` passes in engine-safety, `make run` starts on port 8001

---

## Plan 7: Docker + CI/CD Pipeline
**Wave:** 4 (depends on Plan 4, 5, 6)
**Files to create:**

```
infra/docker/
  Dockerfile.web          # Next.js multi-stage build
  Dockerfile.api          # Fastify multi-stage build
  Dockerfile.engine       # Python engine multi-stage build (shared)
  .dockerignore
docker-compose.yml        # Local dev stack (PG, Redis, ClickHouse)
docker-compose.dev.yml    # Dev overrides (hot reload)
.github/
  workflows/
    ci.yml                # Lint + Test + Typecheck on PRs
    deploy-staging.yml    # Build + Push + Deploy to GKE staging
  dependabot.yml          # Automated dependency updates
  CODEOWNERS              # Code review assignment
```

**Tasks:**
1. Create Dockerfiles — multi-stage with build/runtime separation, non-root users
2. Create `docker-compose.yml` for local dev (PostgreSQL 15, Redis 7, ClickHouse)
3. Create GitHub Actions CI workflow: lint → test → typecheck → build (matrix for Node + Python)
4. Create deploy workflow: build Docker images → push to GCR → apply k8s manifests
5. Create `dependabot.yml` for npm + pip dependency updates
6. Create `CODEOWNERS` file

**Verification:** `docker compose up` starts local dev stack, GitHub Actions CI passes on push

---

## Plan 8: Dev Experience (Scripts + Husky + Commitlint)
**Wave:** 4 (parallel with Plan 7)
**Files to create:**

```
scripts/
  setup.sh                # First-time dev setup script
  seed.sh                 # Seed local databases (placeholder)
.husky/
  pre-commit              # Run lint-staged
  commit-msg              # Commitlint (conventional commits)
.commitlintrc.js          # Conventional commit rules
.lintstagedrc.js          # Lint only staged files
```

**Tasks:**
1. Configure Husky for git hooks
2. Configure commitlint for conventional commits (feat:, fix:, chore:, etc.)
3. Configure lint-staged for pre-commit (ESLint + Prettier on staged .ts/.tsx, Ruff on .py)
4. Create `setup.sh` — install deps, copy .env.example, run docker compose
5. Create `seed.sh` — placeholder for database seeding
6. Add root scripts: `pnpm dev` (runs all services), `pnpm lint`, `pnpm test`, `pnpm build`

**Verification:** Failed commit message `bad commit` is rejected, `pnpm dev` starts all services concurrently

---

## Execution Order

```
Wave 1: Plan 1 (Monorepo root)
Wave 2: Plan 2 (Directories) + Plan 3 (TS/ESLint/Prettier) — parallel
Wave 3: Plan 4 (Next.js) + Plan 5 (Fastify) + Plan 6 (Python template) — parallel
Wave 4: Plan 7 (Docker/CI) + Plan 8 (Dev experience) — parallel
```

## Threat Model (Phase 1 — Minimal)

| Threat | Mitigation |
|--------|-----------|
| Dependency supply chain | Dependabot enabled, lockfile committed, `pnpm audit` in CI |
| Secrets in repo | `.gitignore` covers `.env*`, CI uses GitHub Secrets |
| Docker image bloat | Multi-stage builds, non-root user, .dockerignore |
| Inconsistent code style | ESLint + Prettier + Ruff enforced via pre-commit hooks |

---
*Phase 1 | 8 plans | 4 waves | Zero business logic*
