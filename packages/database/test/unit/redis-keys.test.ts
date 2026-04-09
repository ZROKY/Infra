import { describe, it, expect } from 'vitest';
import { RedisKeys, REDIS_TTL } from '../../src/redis-keys';

describe('RedisKeys', () => {
  it('builds trust score key with client and agent', () => {
    const key = RedisKeys.trustScore('client-123', 'agent-456');
    expect(key).toBe('trust_score:client-123:agent-456');
  });

  it('builds engine scores key', () => {
    const key = RedisKeys.engineScores('c1', 'a1');
    expect(key).toBe('engine_scores:c1:a1');
  });

  it('builds alert count key with 24h suffix', () => {
    const key = RedisKeys.alertCount('client-abc');
    expect(key).toBe('alert_count:client-abc:24h');
  });

  it('builds API rate limit key from hash', () => {
    const key = RedisKeys.apiRateLimit('sha256hash');
    expect(key).toBe('api_rate_limit:sha256hash');
  });

  it('builds client config key', () => {
    const key = RedisKeys.clientConfig('c1');
    expect(key).toBe('client_config:c1');
  });

  it('builds badge score key from agent', () => {
    const key = RedisKeys.badgeScore('agent-789');
    expect(key).toBe('badge_score:agent-789');
  });

  it('builds scan rate key from IP hash', () => {
    const key = RedisKeys.scanRate('iphash');
    expect(key).toBe('scan_rate:iphash');
  });

  it('has correct TTL values', () => {
    expect(REDIS_TTL.TRUST_SCORE).toBe(60);
    expect(REDIS_TTL.ENGINE_SCORES).toBe(60);
    expect(REDIS_TTL.ALERT_COUNT).toBe(86_400);
    expect(REDIS_TTL.API_RATE_LIMIT).toBe(60);
    expect(REDIS_TTL.CLIENT_CONFIG).toBe(300);
    expect(REDIS_TTL.BADGE_SCORE).toBe(30);
    expect(REDIS_TTL.SCAN_RATE).toBe(86_400);
  });
});
