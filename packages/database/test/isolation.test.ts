/**
 * Multi-Tenant Isolation Test
 * Verifies RLS policies prevent cross-client data leakage
 *
 * Requires: PostgreSQL running with migrations applied
 * Run: DATABASE_URL=... pnpm test:isolation
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { Client } from 'pg';

const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://zroky:zroky_dev_password@localhost:5432/zroky';

describe('Multi-Tenant Isolation (RLS)', () => {
  let adminClient: Client;
  let appClient: Client;

  let clientAId: string;
  let clientBId: string;

  beforeAll(async () => {
    // Admin connection (bypasses RLS)
    adminClient = new Client({ connectionString: DATABASE_URL });
    await adminClient.connect();

    // Get two client IDs (requires seed data)
    const { rows } = await adminClient.query(
      "SELECT id, name FROM clients ORDER BY created_at LIMIT 2"
    );

    if (rows.length < 2) {
      throw new Error('Need at least 2 clients for isolation test. Run seed first.');
    }

    clientAId = rows[0].id;
    clientBId = rows[1].id;

    // Create app connection that respects RLS
    appClient = new Client({ connectionString: DATABASE_URL });
    await appClient.connect();
    await appClient.query("SET ROLE zroky_app");
  });

  afterAll(async () => {
    await adminClient?.end();
    await appClient?.end();
  });

  it('Client A cannot see Client B agents', async () => {
    await appClient.query(`SET app.current_client_id = '${clientAId}'`);

    const { rows } = await appClient.query('SELECT * FROM ai_agents');

    // All returned agents must belong to Client A
    for (const row of rows) {
      expect(row.client_id).toBe(clientAId);
    }

    // Verify Client B agents are NOT returned
    const bAgents = rows.filter((r) => r.client_id === clientBId);
    expect(bAgents).toHaveLength(0);
  });

  it('Client B cannot see Client A agents', async () => {
    await appClient.query(`SET app.current_client_id = '${clientBId}'`);

    const { rows } = await appClient.query('SELECT * FROM ai_agents');

    for (const row of rows) {
      expect(row.client_id).toBe(clientBId);
    }

    const aAgents = rows.filter((r) => r.client_id === clientAId);
    expect(aAgents).toHaveLength(0);
  });

  it('Client A cannot see Client B API keys', async () => {
    await appClient.query(`SET app.current_client_id = '${clientAId}'`);

    const { rows } = await appClient.query('SELECT * FROM api_keys');

    for (const row of rows) {
      expect(row.client_id).toBe(clientAId);
    }
  });

  it('Client A cannot see Client B incidents', async () => {
    await appClient.query(`SET app.current_client_id = '${clientAId}'`);

    const { rows } = await appClient.query('SELECT * FROM incidents');

    for (const row of rows) {
      expect(row.client_id).toBe(clientAId);
    }
  });

  it('Client A cannot see Client B users', async () => {
    await appClient.query(`SET app.current_client_id = '${clientAId}'`);

    const { rows } = await appClient.query('SELECT * FROM users');

    for (const row of rows) {
      expect(row.client_id).toBe(clientAId);
    }
  });

  it('Client A cannot INSERT agent for Client B', async () => {
    await appClient.query(`SET app.current_client_id = '${clientAId}'`);

    // Attempt to insert an agent belonging to Client B
    await expect(
      appClient.query(
        `INSERT INTO ai_agents (client_id, name, type)
         VALUES ($1, 'Rogue Agent', 'chatbot')`,
        [clientBId]
      )
    ).rejects.toThrow();
  });

  it('Admin connection bypasses RLS (can see all)', async () => {
    const { rows: allAgents } = await adminClient.query(
      'SELECT DISTINCT client_id FROM ai_agents'
    );

    // Admin should see agents from multiple clients
    const clientIds = allAgents.map((r) => r.client_id);
    expect(clientIds).toContain(clientAId);
    expect(clientIds).toContain(clientBId);
  });
});
