import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { ZrokyClient, ApiError } from '../src/client';
import { ZROKYMonitor } from '../src/monitor';
import { VERSION } from '../src/index';

// ===========================================================================
// Client tests
// ===========================================================================

describe('ZrokyClient', () => {
  it('creates a client instance', () => {
    const client = new ZrokyClient({ apiKey: 'zk_test_123' });
    expect(client).toBeDefined();
  });

  it('rejects empty API key', () => {
    expect(() => new ZrokyClient({ apiKey: '' })).toThrow('apiKey');
  });

  it('uses default URLs', () => {
    const client = new ZrokyClient({ apiKey: 'zk_test_123' });
    expect(client.getBaseUrl()).toBe('https://api.zroky.ai');
  });

  it('strips trailing slash from URLs', () => {
    const client = new ZrokyClient({
      apiKey: 'zk_test_123',
      baseUrl: 'https://custom.api.com/',
    });
    expect(client.getBaseUrl()).toBe('https://custom.api.com');
  });

  it('exposes key prefix for debugging', () => {
    const client = new ZrokyClient({ apiKey: 'zk_test_123456' });
    expect(client.getKeyPrefix()).toBe('zk_test_1234');
  });

  it('sends single event', async () => {
    const mockResponse = new Response(JSON.stringify({ status: 'ok' }), { status: 200 });
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(mockResponse);

    const client = new ZrokyClient({ apiKey: 'zk_test_123' });
    const result = await client.sendEvent({ agent_id: 'test', prompt: 'hi' });
    expect(result).toEqual({ status: 'ok' });

    vi.restoreAllMocks();
  });

  it('sends batch events', async () => {
    const mockResponse = new Response(JSON.stringify({ accepted: 2 }), { status: 200 });
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(mockResponse);

    const client = new ZrokyClient({ apiKey: 'zk_test_123' });
    const result = await client.sendBatch([{ prompt: 'a' }, { prompt: 'b' }]);
    expect(result).toEqual({ accepted: 2 });

    vi.restoreAllMocks();
  });

  it('throws ApiError on 4xx', async () => {
    const mockResponse = new Response('Unauthorized', { status: 401 });
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(mockResponse);

    const client = new ZrokyClient({ apiKey: 'zk_test_123' });
    await expect(client.getTrustScore('agent_abc')).rejects.toThrow(ApiError);

    vi.restoreAllMocks();
  });

  it('fetches trust score', async () => {
    const mockResponse = new Response(
      JSON.stringify({ score: 85, status: 'trusted' }),
      { status: 200 },
    );
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(mockResponse);

    const client = new ZrokyClient({ apiKey: 'zk_test_123' });
    const result = await client.getTrustScore('agent_abc');
    expect(result).toEqual({ score: 85, status: 'trusted' });

    vi.restoreAllMocks();
  });
});

// ===========================================================================
// Monitor tests
// ===========================================================================

describe('ZROKYMonitor', () => {
  let monitor: ZROKYMonitor;

  afterEach(async () => {
    if (monitor) {
      // Force close without flushing
      (monitor as any).closed = true;
      clearInterval((monitor as any).flushTimer);
    }
  });

  it('rejects empty agentId', () => {
    expect(() =>
      new ZROKYMonitor({ apiKey: 'zk_test_123', agentId: '' }),
    ).toThrow('agentId');
  });

  it('queues tracked events', () => {
    monitor = new ZROKYMonitor({ apiKey: 'zk_test_123', agentId: 'test' });
    const result = monitor.track('hello', 'world');
    expect(result).toEqual({ status: 'queued' });
    expect(monitor.queueSize).toBe(1);
  });

  it('throws on track after close', async () => {
    monitor = new ZROKYMonitor({ apiKey: 'zk_test_123', agentId: 'test' });
    (monitor as any).closed = true;
    expect(() => monitor.track('a', 'b')).toThrow('closed');
  });

  it('drops events when queue is full (fail-open)', () => {
    monitor = new ZROKYMonitor({
      apiKey: 'zk_test_123',
      agentId: 'test',
      failOpen: true,
      maxQueueSize: 2,
    });
    monitor.track('a', 'b');
    monitor.track('c', 'd');
    const result = monitor.track('e', 'f');
    expect(result).toEqual({ status: 'dropped', reason: 'queue_full' });
  });

  it('throws when queue is full (fail-closed)', () => {
    monitor = new ZROKYMonitor({
      apiKey: 'zk_test_123',
      agentId: 'test',
      failOpen: false,
      maxQueueSize: 1,
    });
    monitor.track('a', 'b');
    expect(() => monitor.track('c', 'd')).toThrow('queue full');
  });

  it('includes metadata in tracked events', () => {
    monitor = new ZROKYMonitor({ apiKey: 'zk_test_123', agentId: 'test' });
    monitor.track('hello', 'world', {
      model: 'gpt-4',
      sessionId: 'sess_123',
      metadata: { foo: 'bar' },
    });

    const event = (monitor as any).queue[0];
    expect(event.model).toBe('gpt-4');
    expect(event.session_id).toBe('sess_123');
    expect(event.metadata.foo).toBe('bar');
    expect(event.timestamp).toBeGreaterThan(0);
  });

  it('flushes queued events', async () => {
    const mockResponse = new Response(JSON.stringify({ status: 'ok' }), { status: 200 });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(mockResponse);

    monitor = new ZROKYMonitor({ apiKey: 'zk_test_123', agentId: 'test' });
    monitor.track('hello', 'world');
    const count = await monitor.flush();
    expect(count).toBe(1);
    expect(monitor.queueSize).toBe(0);

    vi.restoreAllMocks();
  });

  it('circuit breaker opens after threshold failures', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('network'));

    monitor = new ZROKYMonitor({ apiKey: 'zk_test_123', agentId: 'test' });
    for (let i = 0; i < 5; i++) {
      monitor.track('hello', 'world');
      await monitor.flush();
    }

    expect(monitor.isCircuitOpen).toBe(true);

    vi.restoreAllMocks();
  });
});
