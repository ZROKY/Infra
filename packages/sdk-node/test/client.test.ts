import { describe, it, expect } from 'vitest';

import { ZrokyClient } from '../src/index';

describe('ZrokyClient', () => {
  it('creates a client instance', () => {
    const client = new ZrokyClient({ apiKey: 'zk_test_123' });
    expect(client).toBeDefined();
  });
});
