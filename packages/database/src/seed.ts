/**
 * Dev Seed Script — Creates test data for local development
 * 2 clients, agents, API keys, users
 */
import { Client } from 'pg';
import { createHmac, randomBytes } from 'node:crypto';

const HMAC_SECRET = process.env.API_KEY_HMAC_SECRET || 'zroky-dev-hmac-secret';

function hashApiKey(rawKey: string): string {
  return createHmac('sha256', HMAC_SECRET).update(rawKey).digest('hex');
}

function generateApiKey(type: 'ingest' | 'manage' | 'agent'): { raw: string; hash: string; prefix: string } {
  const raw = `zk_${type}_${randomBytes(24).toString('base64url')}`;
  return {
    raw,
    hash: hashApiKey(raw),
    prefix: raw.substring(0, 12),
  };
}

async function seed() {
  const databaseUrl = process.env.DATABASE_URL || 'postgresql://zroky:zroky_dev_password@localhost:5432/zroky';
  const client = new Client({ connectionString: databaseUrl });
  await client.connect();

  try {
    console.log('🌱 Seeding development data...\n');

    // ── Get free plan ID ──
    const { rows: plans } = await client.query(
      "SELECT id FROM subscription_plans WHERE name = 'developer' LIMIT 1"
    );
    if (plans.length === 0) {
      throw new Error('Run migrations first — subscription_plans table is empty');
    }
    const planId = plans[0].id;

    // ── Client A: Acme Corp ──
    const { rows: [clientA] } = await client.query(
      `INSERT INTO clients (name, plan_id, tier, status)
       VALUES ('Acme Corp', $1, 'developer', 'active')
       ON CONFLICT DO NOTHING
       RETURNING id`,
      [planId]
    );
    const clientAId = clientA?.id;
    if (!clientAId) {
      console.log('Seed data already exists. Skipping.');
      return;
    }
    console.log(`  Client A: ${clientAId} (Acme Corp)`);

    // ── Client B: Globex Inc ──
    const { rows: [clientB] } = await client.query(
      `INSERT INTO clients (name, plan_id, tier, status)
       VALUES ('Globex Inc', $1, 'developer', 'active')
       RETURNING id`,
      [planId]
    );
    const clientBId = clientB.id;
    console.log(`  Client B: ${clientBId} (Globex Inc)`);

    // ── Agents ──
    const { rows: [agentA1] } = await client.query(
      `INSERT INTO ai_agents (client_id, name, type, provider, model_name)
       VALUES ($1, 'Support Bot', 'chatbot', 'openai', 'gpt-4o')
       RETURNING id`,
      [clientAId]
    );
    const { rows: [agentA2] } = await client.query(
      `INSERT INTO ai_agents (client_id, name, type, provider, model_name)
       VALUES ($1, 'RAG Assistant', 'rag', 'anthropic', 'claude-3.5-sonnet')
       RETURNING id`,
      [clientAId]
    );
    const { rows: [agentB1] } = await client.query(
      `INSERT INTO ai_agents (client_id, name, type, provider, model_name)
       VALUES ($1, 'Sales Agent', 'autonomous_agent', 'openai', 'gpt-4o')
       RETURNING id`,
      [clientBId]
    );
    console.log(`  Agents: A1=${agentA1.id}, A2=${agentA2.id}, B1=${agentB1.id}`);

    // ── API Keys ──
    const keyA = generateApiKey('ingest');
    const keyB = generateApiKey('ingest');
    await client.query(
      `INSERT INTO api_keys (client_id, key_hash, key_prefix, key_type, scopes)
       VALUES ($1, $2, $3, 'ingest', ARRAY['write:events'])`,
      [clientAId, keyA.hash, keyA.prefix]
    );
    await client.query(
      `INSERT INTO api_keys (client_id, key_hash, key_prefix, key_type, scopes)
       VALUES ($1, $2, $3, 'ingest', ARRAY['write:events'])`,
      [clientBId, keyB.hash, keyB.prefix]
    );
    console.log(`  API Key A: ${keyA.raw}`);
    console.log(`  API Key B: ${keyB.raw}`);

    // ── Users ──
    await client.query(
      `INSERT INTO users (client_id, email, role)
       VALUES ($1, 'alice@acme.com', 'owner'),
              ($1, 'bob@acme.com', 'engineer')`,
      [clientAId]
    );
    await client.query(
      `INSERT INTO users (client_id, email, role)
       VALUES ($1, 'carol@globex.com', 'owner')`,
      [clientBId]
    );
    console.log(`  Users: alice@acme (owner), bob@acme (engineer), carol@globex (owner)`);

    // ── Alert Rules ──
    await client.query(
      `INSERT INTO alert_rules (client_id, agent_id, engine, condition_type, threshold_value, severity)
       VALUES ($1, $2, 'safety', 'threshold', 40.00, 'critical')`,
      [clientAId, agentA1.id]
    );

    console.log('\n✅ Seed complete!');
    console.log('\n⚠️  Save these API keys — they cannot be retrieved later:');
    console.log(`  Acme:   ${keyA.raw}`);
    console.log(`  Globex: ${keyB.raw}`);

  } finally {
    await client.end();
  }
}

seed().catch((err) => {
  console.error('Seed failed:', err);
  process.exit(1);
});
