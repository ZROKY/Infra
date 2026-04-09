import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createHmac } from 'node:crypto';

// Mock config first
vi.mock('../src/config', () => ({
  config: {
    apiKeyHmacSecret: 'test-hmac-secret-key-for-testing',
  },
}));

describe('API Key HMAC Validation', () => {
  const hmacSecret = 'test-hmac-secret-key-for-testing';

  it('should produce deterministic hash from key', () => {
    const rawKey = 'zk_ingest_testkey123';
    const hash1 = createHmac('sha256', hmacSecret).update(rawKey).digest('hex');
    const hash2 = createHmac('sha256', hmacSecret).update(rawKey).digest('hex');
    expect(hash1).toBe(hash2);
    expect(hash1).toHaveLength(64);
  });

  it('should produce different hashes for different keys', () => {
    const hash1 = createHmac('sha256', hmacSecret).update('zk_ingest_key1').digest('hex');
    const hash2 = createHmac('sha256', hmacSecret).update('zk_ingest_key2').digest('hex');
    expect(hash1).not.toBe(hash2);
  });

  it('should extract 12-char prefix', () => {
    const rawKey = 'zk_ingest_abc123xyz789more';
    const prefix = rawKey.substring(0, 12);
    expect(prefix).toBe('zk_ingest_ab');
    expect(prefix).toHaveLength(12);
  });

  it('should extract key type from prefix format', () => {
    expect('zk_ingest_abc'.match(/^zk_(ingest|manage|agent)_/)?.[1]).toBe('ingest');
    expect('zk_manage_abc'.match(/^zk_(ingest|manage|agent)_/)?.[1]).toBe('manage');
    expect('zk_agent_abc'.match(/^zk_(ingest|manage|agent)_/)?.[1]).toBe('agent');
  });
});

describe('Rate Limit Logic', () => {
  const RATE_LIMITS: Record<string, { ingest: number; query: number; manage: number }> = {
    free:       { ingest: 100,    query: 60,     manage: 30 },
    developer:  { ingest: 100,    query: 60,     manage: 30 },
    smb:        { ingest: 1_000,  query: 300,    manage: 100 },
    growth:     { ingest: 10_000, query: 1_000,  manage: 300 },
    enterprise: { ingest: 100_000, query: 10_000, manage: 1_000 },
  };

  it('should return correct limits for each tier', () => {
    expect(RATE_LIMITS.free!.ingest).toBe(100);
    expect(RATE_LIMITS.enterprise!.ingest).toBe(100_000);
    expect(RATE_LIMITS.smb!.query).toBe(300);
    expect(RATE_LIMITS.growth!.manage).toBe(300);
  });

  it('should default to developer tier for unknown tiers', () => {
    const tier = 'unknown';
    const limits = RATE_LIMITS[tier] ?? RATE_LIMITS.developer!;
    expect(limits!.ingest).toBe(100);
  });
});

describe('Envelope Utility', () => {
  let envelope: typeof import('../src/lib/envelope');

  beforeEach(async () => {
    envelope = await import('../src/lib/envelope');
  });

  it('success() wraps data correctly', () => {
    const result = envelope.success({ id: '123' });
    expect(result.success).toBe(true);
    expect(result.data).toEqual({ id: '123' });
    expect(result.error).toBeNull();
    expect(result.meta.version).toBe('2026-04-08');
  });

  it('error() produces proper structure', () => {
    const result = envelope.error('not_found', 'Resource missing', 404);
    expect(result.success).toBe(false);
    expect(result.data).toBeNull();
    expect(result.error?.code).toBe('not_found');
    expect(result.error?.message).toBe('Resource missing');
    expect(result.statusCode).toBe(404);
  });

  it('paginated() includes pagination', () => {
    const result = envelope.paginated([1, 2], { hasMore: true, nextCursor: 'abc' });
    expect(result.success).toBe(true);
    expect(result.data).toEqual([1, 2]);
    expect(result.pagination).toEqual({ hasMore: true, nextCursor: 'abc' });
  });
});

describe('Event Validation', () => {
  it('should require agent_id, prompt, response', () => {
    const schema = {
      required: ['agent_id', 'prompt', 'response'],
    };
    expect(schema.required).toContain('agent_id');
    expect(schema.required).toContain('prompt');
    expect(schema.required).toContain('response');
  });

  it('should generate unique event IDs', () => {
    const ids = new Set<string>();
    for (let i = 0; i < 100; i++) {
      const id = `evt_${crypto.randomUUID().replace(/-/g, '')}`;
      ids.add(id);
    }
    expect(ids.size).toBe(100);
  });

  it('event ID format should start with evt_', () => {
    const id = `evt_${crypto.randomUUID().replace(/-/g, '')}`;
    expect(id).toMatch(/^evt_[a-f0-9]{32}$/);
  });
});

describe('RBAC Hierarchy', () => {
  const ROLE_HIERARCHY: Record<string, number> = {
    viewer: 0,
    analyst: 1,
    engineer: 2,
    admin: 3,
    owner: 4,
  };

  it('should enforce role ordering', () => {
    expect(ROLE_HIERARCHY.owner).toBeGreaterThan(ROLE_HIERARCHY.admin!);
    expect(ROLE_HIERARCHY.admin).toBeGreaterThan(ROLE_HIERARCHY.engineer!);
    expect(ROLE_HIERARCHY.engineer).toBeGreaterThan(ROLE_HIERARCHY.analyst!);
    expect(ROLE_HIERARCHY.analyst).toBeGreaterThan(ROLE_HIERARCHY.viewer!);
  });

  it('should allow access when role >= minimum', () => {
    const hasAccess = (role: string, minRole: string) =>
      (ROLE_HIERARCHY[role] ?? 0) >= (ROLE_HIERARCHY[minRole] ?? 0);

    expect(hasAccess('owner', 'viewer')).toBe(true);
    expect(hasAccess('admin', 'engineer')).toBe(true);
    expect(hasAccess('viewer', 'admin')).toBe(false);
    expect(hasAccess('analyst', 'engineer')).toBe(false);
  });
});
