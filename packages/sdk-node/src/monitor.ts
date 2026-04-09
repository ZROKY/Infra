/**
 * ZROKY Monitor — high-level async event tracker with batching and fail-open.
 */

import { ZrokyClient, ZrokyClientConfig } from './client';

const DEFAULT_BATCH_SIZE = 50;
const DEFAULT_FLUSH_INTERVAL = 5_000;
const DEFAULT_MAX_QUEUE = 10_000;
const CIRCUIT_BREAKER_THRESHOLD = 5;
const CIRCUIT_BREAKER_COOLDOWN = 60_000;

export interface MonitorConfig extends ZrokyClientConfig {
  agentId: string;
  failOpen?: boolean;
  batchSize?: number;
  flushInterval?: number;
  maxQueueSize?: number;
}

export interface TrackOptions {
  model?: string;
  sessionId?: string;
  metadata?: Record<string, unknown>;
}

export type TrackResult =
  | { status: 'queued' }
  | { status: 'dropped'; reason: string };

interface QueuedEvent {
  agent_id: string;
  prompt: string;
  response: string;
  model: string;
  session_id: string;
  metadata: Record<string, unknown>;
  timestamp: number;
}

export class ZROKYMonitor {
  private readonly client: ZrokyClient;
  private readonly agentId: string;
  private readonly failOpen: boolean;
  private readonly batchSize: number;
  private readonly maxQueueSize: number;
  private queue: QueuedEvent[] = [];
  private closed = false;
  private flushTimer: ReturnType<typeof setInterval>;

  // Circuit breaker
  private consecutiveFailures = 0;
  private circuitOpenUntil = 0;

  constructor(config: MonitorConfig) {
    if (!config.agentId) {
      throw new Error('agentId is required');
    }

    this.agentId = config.agentId;
    this.failOpen = config.failOpen ?? true;
    this.batchSize = config.batchSize || DEFAULT_BATCH_SIZE;
    this.maxQueueSize = config.maxQueueSize || DEFAULT_MAX_QUEUE;
    this.client = new ZrokyClient(config);

    const interval = config.flushInterval || DEFAULT_FLUSH_INTERVAL;
    this.flushTimer = setInterval(() => this.flushAll(), interval);
    // Allow Node.js to exit even if timer is running
    if (this.flushTimer.unref) {
      this.flushTimer.unref();
    }
  }

  track(prompt: string, response: string, options: TrackOptions = {}): TrackResult {
    if (this.closed) {
      throw new Error('Monitor is closed');
    }

    if (this.queue.length >= this.maxQueueSize) {
      if (this.failOpen) {
        return { status: 'dropped', reason: 'queue_full' };
      }
      throw new Error(`ZROKY event queue full (${this.maxQueueSize})`);
    }

    this.queue.push({
      agent_id: this.agentId,
      prompt,
      response,
      model: options.model || '',
      session_id: options.sessionId || '',
      metadata: options.metadata || {},
      timestamp: Date.now() / 1000,
    });

    return { status: 'queued' };
  }

  async flush(): Promise<number> {
    if (this.queue.length === 0) return 0;

    const batch = this.queue.splice(0, this.batchSize);
    return this.sendBatch(batch);
  }

  async close(): Promise<void> {
    if (this.closed) return;
    this.closed = true;
    clearInterval(this.flushTimer);

    while (this.queue.length > 0) {
      const batch = this.queue.splice(0, this.batchSize);
      await this.sendBatch(batch);
    }
  }

  get queueSize(): number {
    return this.queue.length;
  }

  get isCircuitOpen(): boolean {
    return this.circuitOpenUntil > Date.now();
  }

  // -- Internal ------------------------------------------------------------

  private async flushAll(): Promise<void> {
    try {
      while (this.queue.length > 0) {
        const batch = this.queue.splice(0, this.batchSize);
        await this.sendBatch(batch);
      }
    } catch {
      // fail-open: swallow errors in background flush
    }
  }

  private async sendBatch(events: QueuedEvent[]): Promise<number> {
    if (events.length === 0) return 0;

    // Circuit breaker check
    if (this.circuitOpenUntil > Date.now()) {
      this.queue.unshift(...events);
      return 0;
    }

    try {
      if (events.length === 1) {
        await this.client.sendEvent(events[0] as unknown as Record<string, unknown>);
      } else {
        await this.client.sendBatch(
          events as unknown as Record<string, unknown>[],
        );
      }
      this.consecutiveFailures = 0;
      return events.length;
    } catch {
      this.consecutiveFailures++;
      if (this.consecutiveFailures >= CIRCUIT_BREAKER_THRESHOLD) {
        this.circuitOpenUntil = Date.now() + CIRCUIT_BREAKER_COOLDOWN;
      }

      if (this.failOpen) {
        this.queue.unshift(...events);
        return 0;
      }
      throw new Error('ZROKY send failed');
    }
  }
}
