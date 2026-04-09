import { describe, it, expect } from 'vitest';

import { buildApp } from '../src/app';

describe('Health endpoint', () => {
  it('GET /health returns 200 with ok status', async () => {
    const app = await buildApp();

    const response = await app.inject({
      method: 'GET',
      url: '/health',
    });

    expect(response.statusCode).toBe(200);

    const body = JSON.parse(response.body);
    expect(body.success).toBe(true);
    expect(body.data.status).toBe('ok');
    expect(body.data.version).toBe('1.0.0');
    expect(body.meta.requestId).toBeDefined();
    expect(body.meta.timestamp).toBeDefined();
  });
});
