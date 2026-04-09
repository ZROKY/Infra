FROM node:20-alpine AS base

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

# ── Dependencies ──────────────────────────────
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY services/api/package.json services/api/
COPY packages/database/package.json packages/database/
COPY packages/shared/package.json packages/shared/
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile --prod

# ── Build ─────────────────────────────────────
FROM base AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY services/api/ services/api/
COPY packages/database/ packages/database/
COPY packages/shared/ packages/shared/
COPY tsconfig.base.json ./
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm --filter @zroky/api build

# ── Production ────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3001

# Security: non-root user
RUN addgroup --system --gid 1001 zroky && \
    adduser --system --uid 1001 zroky

COPY --from=deps --chown=zroky:zroky /app/node_modules ./node_modules
COPY --from=deps --chown=zroky:zroky /app/services/api/node_modules ./services/api/node_modules
COPY --from=build --chown=zroky:zroky /app/services/api/dist ./services/api/dist
COPY --from=build --chown=zroky:zroky /app/services/api/package.json ./services/api/

USER zroky

EXPOSE 3001

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3001/v1/health || exit 1

CMD ["node", "services/api/dist/server.js"]
