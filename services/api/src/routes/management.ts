import { createHmac, randomBytes } from 'node:crypto';

import type { FastifyInstance } from 'fastify';

import { requireApiKey, type AuthenticatedRequest } from '../middleware/auth';
import { rateLimit } from '../middleware/rate-limit';
import { success, paginated, error } from '../lib/envelope';
import { getPool } from '../lib/db';
import { config } from '../config';

export async function agentRoutes(app: FastifyInstance) {
  const preHandler = [requireApiKey('manage'), rateLimit('manage')];

  // POST /v1/agents
  app.post<{
    Body: { name: string; type?: string; provider?: string; model_name?: string; integration_type?: string };
  }>(
    '/v1/agents',
    {
      preHandler,
      schema: {
        body: {
          type: 'object',
          required: ['name'],
          properties: {
            name: { type: 'string', minLength: 1, maxLength: 255 },
            type: { type: 'string', enum: ['chatbot', 'rag', 'autonomous_agent', 'multi_agent'] },
            provider: { type: 'string', maxLength: 100 },
            model_name: { type: 'string', maxLength: 100 },
            integration_type: { type: 'string', enum: ['sdk', 'proxy', 'webhook'] },
          },
        },
      },
    },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const { name, type = 'chatbot', provider, model_name, integration_type = 'sdk' } = request.body;

      const pool = getPool();
      try {
        const { rows } = await pool.query(
          `INSERT INTO ai_agents (client_id, name, type, provider, model_name, integration_type)
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
          [apiKey.clientId, name, type, provider || null, model_name || null, integration_type],
        );
        return reply.status(201).send(success(rows[0]));
      } catch (err: unknown) {
        if ((err as { code?: string }).code === '23505') {
          return reply.status(409).send(error('conflict', 'An agent with this name already exists', 409));
        }
        throw err;
      }
    },
  );

  // GET /v1/agents
  app.get<{ Querystring: { cursor?: string; limit?: number } }>(
    '/v1/agents',
    {
      preHandler,
      schema: {
        querystring: {
          type: 'object',
          properties: {
            cursor: { type: 'string' },
            limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          },
        },
      },
    },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const limit = request.query.limit || 20;
      const cursor = request.query.cursor;

      const pool = getPool();
      let query = 'SELECT * FROM ai_agents WHERE client_id = $1';
      const params: unknown[] = [apiKey.clientId];

      if (cursor) {
        query += ' AND created_at < $2';
        params.push(new Date(cursor));
      }

      query += ' ORDER BY created_at DESC LIMIT $' + (params.length + 1);
      params.push(limit + 1); // Fetch one extra to check hasMore

      const { rows } = await pool.query(query, params);
      const hasMore = rows.length > limit;
      const data = hasMore ? rows.slice(0, limit) : rows;
      const nextCursor = hasMore ? data[data.length - 1].created_at : undefined;

      return reply.send(paginated(data, { hasMore, nextCursor }));
    },
  );

  // GET /v1/agents/:id
  app.get<{ Params: { id: string } }>(
    '/v1/agents/:id',
    { preHandler },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const pool = getPool();
      const { rows } = await pool.query(
        'SELECT * FROM ai_agents WHERE id = $1 AND client_id = $2',
        [request.params.id, apiKey.clientId],
      );
      if (rows.length === 0) {
        return reply.status(404).send(error('not_found', 'Agent not found', 404));
      }
      return reply.send(success(rows[0]));
    },
  );

  // PATCH /v1/agents/:id
  app.patch<{
    Params: { id: string };
    Body: { name?: string; type?: string; provider?: string; model_name?: string; trust_score_threshold?: number };
  }>(
    '/v1/agents/:id',
    {
      preHandler,
      schema: {
        body: {
          type: 'object',
          properties: {
            name: { type: 'string', minLength: 1, maxLength: 255 },
            type: { type: 'string', enum: ['chatbot', 'rag', 'autonomous_agent', 'multi_agent'] },
            provider: { type: 'string', maxLength: 100 },
            model_name: { type: 'string', maxLength: 100 },
            trust_score_threshold: { type: 'integer', minimum: 0, maximum: 100 },
          },
        },
      },
    },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const updates = request.body;
      const fields = Object.entries(updates).filter(([, v]) => v !== undefined);

      if (fields.length === 0) {
        return reply.status(400).send(error('bad_request', 'No fields to update', 400));
      }

      const setClauses = fields.map(([key], i) => `${key} = $${i + 3}`);
      const values = fields.map(([, v]) => v);

      const pool = getPool();
      const { rows } = await pool.query(
        `UPDATE ai_agents SET ${setClauses.join(', ')}
         WHERE id = $1 AND client_id = $2 RETURNING *`,
        [request.params.id, apiKey.clientId, ...values],
      );

      if (rows.length === 0) {
        return reply.status(404).send(error('not_found', 'Agent not found', 404));
      }

      return reply.send(success(rows[0]));
    },
  );

  // DELETE /v1/agents/:id
  app.delete<{ Params: { id: string } }>(
    '/v1/agents/:id',
    { preHandler },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const pool = getPool();
      const { rowCount } = await pool.query(
        'DELETE FROM ai_agents WHERE id = $1 AND client_id = $2',
        [request.params.id, apiKey.clientId],
      );
      if (rowCount === 0) {
        return reply.status(404).send(error('not_found', 'Agent not found', 404));
      }
      return reply.status(204).send();
    },
  );
}

export async function alertRuleRoutes(app: FastifyInstance) {
  const preHandler = [requireApiKey('manage'), rateLimit('manage')];

  // POST /v1/alert-rules
  app.post<{
    Body: {
      agent_id: string;
      engine: string;
      condition_type?: string;
      threshold_value: number;
      severity?: string;
      notification_channels?: Record<string, boolean>;
    };
  }>(
    '/v1/alert-rules',
    {
      preHandler,
      schema: {
        body: {
          type: 'object',
          required: ['agent_id', 'engine', 'threshold_value'],
          properties: {
            agent_id: { type: 'string', format: 'uuid' },
            engine: { type: 'string', enum: ['safety', 'grounding', 'consistency', 'system'] },
            condition_type: { type: 'string', enum: ['threshold', 'drift', 'anomaly'] },
            threshold_value: { type: 'number', minimum: 0, maximum: 100 },
            severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
            notification_channels: { type: 'object' },
          },
        },
      },
    },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const body = request.body;

      const pool = getPool();
      const { rows } = await pool.query(
        `INSERT INTO alert_rules (client_id, agent_id, engine, condition_type, threshold_value, severity, notification_channels)
         VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *`,
        [
          apiKey.clientId,
          body.agent_id,
          body.engine,
          body.condition_type || 'threshold',
          body.threshold_value,
          body.severity || 'medium',
          JSON.stringify(body.notification_channels || { slack: true, email: true }),
        ],
      );

      return reply.status(201).send(success(rows[0]));
    },
  );

  // GET /v1/alert-rules
  app.get(
    '/v1/alert-rules',
    { preHandler },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const pool = getPool();
      const { rows } = await pool.query(
        'SELECT * FROM alert_rules WHERE client_id = $1 ORDER BY created_at DESC',
        [apiKey.clientId],
      );
      return reply.send(success(rows));
    },
  );

  // PATCH /v1/alert-rules/:id
  app.patch<{
    Params: { id: string };
    Body: { threshold_value?: number; severity?: string; enabled?: boolean; notification_channels?: Record<string, boolean> };
  }>(
    '/v1/alert-rules/:id',
    { preHandler },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const updates = request.body;
      const fields = Object.entries(updates).filter(([, v]) => v !== undefined);

      if (fields.length === 0) {
        return reply.status(400).send(error('bad_request', 'No fields to update', 400));
      }

      const setClauses = fields.map(([key], i) => {
        if (key === 'notification_channels') return `${key} = $${i + 3}::jsonb`;
        return `${key} = $${i + 3}`;
      });
      const values = fields.map(([key, v]) => key === 'notification_channels' ? JSON.stringify(v) : v);

      const pool = getPool();
      const { rows } = await pool.query(
        `UPDATE alert_rules SET ${setClauses.join(', ')}
         WHERE id = $1 AND client_id = $2 RETURNING *`,
        [request.params.id, apiKey.clientId, ...values],
      );

      if (rows.length === 0) {
        return reply.status(404).send(error('not_found', 'Alert rule not found', 404));
      }
      return reply.send(success(rows[0]));
    },
  );

  // DELETE /v1/alert-rules/:id
  app.delete<{ Params: { id: string } }>(
    '/v1/alert-rules/:id',
    { preHandler },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const pool = getPool();
      const { rowCount } = await pool.query(
        'DELETE FROM alert_rules WHERE id = $1 AND client_id = $2',
        [request.params.id, apiKey.clientId],
      );
      if (rowCount === 0) {
        return reply.status(404).send(error('not_found', 'Alert rule not found', 404));
      }
      return reply.status(204).send();
    },
  );
}

export async function apiKeyRoutes(app: FastifyInstance) {
  const preHandler = [requireApiKey('manage'), rateLimit('manage')];

  // POST /v1/api-keys — Create new API key
  app.post<{
    Body: { key_type: 'ingest' | 'manage' | 'agent'; scopes?: string[]; agent_id?: string };
  }>(
    '/v1/api-keys',
    {
      preHandler,
      schema: {
        body: {
          type: 'object',
          required: ['key_type'],
          properties: {
            key_type: { type: 'string', enum: ['ingest', 'manage', 'agent'] },
            scopes: { type: 'array', items: { type: 'string' } },
            agent_id: { type: 'string', format: 'uuid' },
          },
        },
      },
    },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const { key_type, scopes = [], agent_id } = request.body;

      if (key_type === 'agent' && !agent_id) {
        return reply.status(400).send(
          error('bad_request', 'agent_id is required for agent-scoped keys', 400),
        );
      }

      // Check max 5 active keys limit
      const pool = getPool();
      const { rows: countRows } = await pool.query(
        'SELECT COUNT(*) as cnt FROM api_keys WHERE client_id = $1 AND revoked_at IS NULL',
        [apiKey.clientId],
      );
      if (parseInt(countRows[0].cnt) >= 5) {
        return reply.status(400).send(
          error('limit_exceeded', 'Maximum 5 active API keys per client. Revoke an existing key first.', 400),
        );
      }

      // Generate key
      const rawKey = `zk_${key_type}_${randomBytes(24).toString('base64url')}`;
      const keyHash = createHmac('sha256', config.apiKeyHmacSecret).update(rawKey).digest('hex');
      const keyPrefix = rawKey.substring(0, 12);

      const { rows } = await pool.query(
        `INSERT INTO api_keys (client_id, key_hash, key_prefix, key_type, scopes, agent_id)
         VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, key_prefix, key_type, scopes, created_at`,
        [apiKey.clientId, keyHash, keyPrefix, key_type, scopes, agent_id || null],
      );

      return reply.status(201).send(
        success({
          ...rows[0],
          // Return raw key ONCE — it cannot be retrieved later
          key: rawKey,
          warning: 'Save this key now. It cannot be retrieved again.',
        }),
      );
    },
  );

  // GET /v1/api-keys — List keys (prefix only, never the hash)
  app.get(
    '/v1/api-keys',
    { preHandler },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const pool = getPool();
      const { rows } = await pool.query(
        `SELECT id, key_prefix, key_type, scopes, agent_id, last_used_at, expires_at, created_at
         FROM api_keys
         WHERE client_id = $1 AND revoked_at IS NULL
         ORDER BY created_at DESC`,
        [apiKey.clientId],
      );
      return reply.send(success(rows));
    },
  );

  // DELETE /v1/api-keys/:id — Revoke key
  app.delete<{ Params: { id: string } }>(
    '/v1/api-keys/:id',
    { preHandler },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const pool = getPool();
      const { rowCount } = await pool.query(
        `UPDATE api_keys SET revoked_at = NOW()
         WHERE id = $1 AND client_id = $2 AND revoked_at IS NULL`,
        [request.params.id, apiKey.clientId],
      );
      if (rowCount === 0) {
        return reply.status(404).send(error('not_found', 'API key not found or already revoked', 404));
      }

      // Invalidate Redis cache
      const { rows } = await pool.query('SELECT key_hash FROM api_keys WHERE id = $1', [request.params.id]);
      if (rows[0]) {
        const redis = (await import('../lib/redis')).getRedis();
        await redis.del(`api_key_cache:${rows[0].key_hash}`);
      }

      return reply.status(204).send();
    },
  );
}

export async function incidentRoutes(app: FastifyInstance) {
  const preHandler = [requireApiKey('manage'), rateLimit('query')];

  // GET /v1/incidents
  app.get<{
    Querystring: { agent_id?: string; status?: string; severity?: string; cursor?: string; limit?: number };
  }>(
    '/v1/incidents',
    {
      preHandler,
      schema: {
        querystring: {
          type: 'object',
          properties: {
            agent_id: { type: 'string', format: 'uuid' },
            status: { type: 'string', enum: ['open', 'investigating', 'resolved', 'dismissed'] },
            severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
            cursor: { type: 'string' },
            limit: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          },
        },
      },
    },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const { agent_id, status, severity, cursor, limit = 20 } = request.query;

      let query = 'SELECT * FROM incidents WHERE client_id = $1';
      const params: unknown[] = [apiKey.clientId];
      let idx = 2;

      if (agent_id) { query += ` AND agent_id = $${idx++}`; params.push(agent_id); }
      if (status) { query += ` AND status = $${idx++}`; params.push(status); }
      if (severity) { query += ` AND severity = $${idx++}`; params.push(severity); }
      if (cursor) { query += ` AND created_at < $${idx++}`; params.push(new Date(cursor)); }

      query += ` ORDER BY created_at DESC LIMIT $${idx}`;
      params.push(limit + 1);

      const pool = getPool();
      const { rows } = await pool.query(query, params);
      const hasMore = rows.length > limit;
      const data = hasMore ? rows.slice(0, limit) : rows;
      const nextCursor = hasMore ? data[data.length - 1].created_at : undefined;

      return reply.send(paginated(data, { hasMore, nextCursor }));
    },
  );

  // GET /v1/incidents/:id
  app.get<{ Params: { id: string } }>(
    '/v1/incidents/:id',
    { preHandler },
    async (request, reply) => {
      const { apiKey } = request as AuthenticatedRequest;
      const pool = getPool();
      const { rows } = await pool.query(
        'SELECT * FROM incidents WHERE id = $1 AND client_id = $2',
        [request.params.id, apiKey.clientId],
      );
      if (rows.length === 0) {
        return reply.status(404).send(error('not_found', 'Incident not found', 404));
      }
      return reply.send(success(rows[0]));
    },
  );
}
