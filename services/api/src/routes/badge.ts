import type { FastifyInstance } from 'fastify';

import { success, error } from '../lib/envelope';
import { getRedis } from '../lib/redis';

// ---------------------------------------------------------------------------
// SVG Badge Generator
// ---------------------------------------------------------------------------

function getStatusColor(score: number): string {
  if (score >= 80) return '#22c55e'; // green
  if (score >= 60) return '#eab308'; // amber
  if (score >= 40) return '#f97316'; // orange
  return '#ef4444'; // red
}

function getStatusLabel(score: number): string {
  if (score >= 80) return 'Trusted';
  if (score >= 60) return 'Moderate';
  if (score >= 40) return 'Low Trust';
  return 'Untrusted';
}

function renderBadgeSvg(
  score: number,
  agentName?: string,
  coverageWarning?: boolean,
): string {
  const color = getStatusColor(score);
  const status = getStatusLabel(score);
  const label = agentName ? `ZROKY | ${agentName}` : 'ZROKY Trust Score';
  const labelWidth = Math.max(120, label.length * 7);
  const valueWidth = 80;
  const totalWidth = labelWidth + valueWidth;
  const warningText = coverageWarning ? ' ⚠' : '';

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${totalWidth}" height="28" role="img" aria-label="${label}: ${score}">
  <title>${label}: ${score} — ${status}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".7"/>
    <stop offset=".1" stop-color="#aaa" stop-opacity=".1"/>
    <stop offset=".9" stop-color="#000" stop-opacity=".3"/>
    <stop offset="1" stop-color="#000" stop-opacity=".5"/>
  </linearGradient>
  <clipPath id="r"><rect width="${totalWidth}" height="28" rx="5" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="${labelWidth}" height="28" fill="#1e293b"/>
    <rect x="${labelWidth}" width="${valueWidth}" height="28" fill="${color}"/>
    <rect width="${totalWidth}" height="28" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="${labelWidth / 2}" y="19.5" fill="#010101" fill-opacity=".3">${label}</text>
    <text x="${labelWidth / 2}" y="18.5">${label}</text>
    <text x="${labelWidth + valueWidth / 2}" y="19.5" fill="#010101" fill-opacity=".3">${score}${warningText}</text>
    <text x="${labelWidth + valueWidth / 2}" y="18.5" font-weight="bold">${score}${warningText}</text>
  </g>
</svg>`;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export async function badgeRoutes(app: FastifyInstance) {
  /**
   * GET /v1/badge/:agentId — JSON badge data (cached 30s)
   */
  app.get<{ Params: { agentId: string } }>(
    '/v1/badge/:agentId',
    {
      schema: {
        params: {
          type: 'object',
          required: ['agentId'],
          properties: {
            agentId: { type: 'string', format: 'uuid' },
          },
        },
      },
    },
    async (request, reply) => {
      const { agentId } = request.params;
      const redis = getRedis();
      const cached = await redis.get(`badge_score:${agentId}`);

      if (!cached) {
        return reply.status(404).send(
          error('not_found', 'Badge not found or not enabled for this agent', 404),
        );
      }

      const badge = JSON.parse(cached);
      reply.header('Cache-Control', 'public, max-age=30');
      return reply.send(success(badge));
    },
  );

  /**
   * GET /v1/badge/:agentId/svg — Embeddable SVG badge widget
   * Public, CDN-cacheable, updates every 5 minutes.
   */
  app.get<{ Params: { agentId: string }; Querystring: { name?: string } }>(
    '/v1/badge/:agentId/svg',
    {
      schema: {
        params: {
          type: 'object',
          required: ['agentId'],
          properties: {
            agentId: { type: 'string', format: 'uuid' },
          },
        },
      },
    },
    async (request, reply) => {
      const { agentId } = request.params;
      const agentName = request.query.name;
      const redis = getRedis();
      const cached = await redis.get(`badge_score:${agentId}`);

      if (!cached) {
        // Return a "not found" badge
        const svg = renderBadgeSvg(0, agentName);
        reply.header('Content-Type', 'image/svg+xml');
        reply.header('Cache-Control', 'public, max-age=60');
        return reply.send(svg);
      }

      const badge = JSON.parse(cached);
      const score = badge.score ?? 0;
      const coverageWarning = (badge.coverage ?? 100) < 50;

      const svg = renderBadgeSvg(score, agentName, coverageWarning);
      reply.header('Content-Type', 'image/svg+xml');
      reply.header('Cache-Control', 'public, max-age=300'); // 5 min CDN cache
      return reply.send(svg);
    },
  );

  /**
   * GET /v1/badge/:agentId/embed — Returns HTML embed snippet
   */
  app.get<{ Params: { agentId: string } }>(
    '/v1/badge/:agentId/embed',
    {
      schema: {
        params: {
          type: 'object',
          required: ['agentId'],
          properties: {
            agentId: { type: 'string', format: 'uuid' },
          },
        },
      },
    },
    async (request, reply) => {
      const { agentId } = request.params;
      const baseUrl = process.env.BADGE_BASE_URL || 'https://badge.zroky.ai';

      return reply.send(
        success({
          html: `<a href="https://app.zroky.ai/agents/${agentId}" target="_blank" rel="noopener"><img src="${baseUrl}/v1/badge/${agentId}/svg" alt="ZROKY Trust Score" /></a>`,
          markdown: `[![ZROKY Trust Score](${baseUrl}/v1/badge/${agentId}/svg)](https://app.zroky.ai/agents/${agentId})`,
          image_url: `${baseUrl}/v1/badge/${agentId}/svg`,
        }),
      );
    },
  );
}
