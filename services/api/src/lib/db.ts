import { Pool } from 'pg';

import { config } from '../config';

let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      connectionString: config.databaseUrl,
      max: 20,
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 5_000,
    });
  }
  return pool;
}

/** Set app.current_client_id for RLS policies */
export async function withClientScope<T>(
  clientId: string,
  fn: (pool: Pool) => Promise<T>,
): Promise<T> {
  const db = getPool();
  const client = await db.connect();
  try {
    await client.query(`SET LOCAL app.current_client_id = '${clientId}'`);
    const result = await fn(client as unknown as Pool);
    return result;
  } finally {
    client.release();
  }
}

export async function closePool(): Promise<void> {
  if (pool) {
    await pool.end();
    pool = null;
  }
}
