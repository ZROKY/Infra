/**
 * ZROKY REST API client — low-level HTTP wrapper for Node.js.
 */

import { VERSION } from './index';

const DEFAULT_BASE_URL = 'https://api.zroky.ai';
const DEFAULT_INGEST_URL = 'https://ingest.zroky.ai';
const DEFAULT_TIMEOUT = 10_000;

export interface ZrokyClientConfig {
  apiKey: string;
  baseUrl?: string;
  ingestUrl?: string;
  timeout?: number;
}

export class ApiError extends Error {
  constructor(
    public readonly statusCode: number,
    message: string,
  ) {
    super(`ZROKY API ${statusCode}: ${message}`);
    this.name = 'ApiError';
  }
}

export class ZrokyClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly ingestUrl: string;
  private readonly timeout: number;
  private readonly headers: Record<string, string>;

  constructor(config: ZrokyClientConfig) {
    if (!config.apiKey) {
      throw new Error('apiKey is required');
    }
    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
    this.ingestUrl = (config.ingestUrl || DEFAULT_INGEST_URL).replace(/\/$/, '');
    this.timeout = config.timeout || DEFAULT_TIMEOUT;
    this.headers = {
      Authorization: `Bearer ${this.apiKey}`,
      'User-Agent': `zroky-node/${VERSION}`,
      'Content-Type': 'application/json',
    };
  }

  // -- Ingestion -----------------------------------------------------------

  async sendEvent(event: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.post(`${this.ingestUrl}/v1/events`, event);
  }

  async sendBatch(events: Record<string, unknown>[]): Promise<Record<string, unknown>> {
    return this.post(`${this.ingestUrl}/v1/events/batch`, { events });
  }

  // -- Query ---------------------------------------------------------------

  async getTrustScore(agentId: string): Promise<Record<string, unknown>> {
    return this.get(`${this.baseUrl}/v1/trust-score/${agentId}`);
  }

  async getTrustScoreHistory(
    agentId: string,
    period = '30d',
    granularity = '1h',
  ): Promise<Record<string, unknown>> {
    const params = new URLSearchParams({ period, granularity });
    return this.get(`${this.baseUrl}/v1/trust-score/${agentId}/history?${params}`);
  }

  async getIncidents(
    agentId?: string,
    params?: Record<string, string>,
  ): Promise<Record<string, unknown>> {
    const searchParams = new URLSearchParams(params);
    if (agentId) searchParams.set('agent_id', agentId);
    return this.get(`${this.baseUrl}/v1/incidents?${searchParams}`);
  }

  // -- HTTP helpers --------------------------------------------------------

  private async get(url: string): Promise<Record<string, unknown>> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const resp = await fetch(url, {
        method: 'GET',
        headers: this.headers,
        signal: controller.signal,
      });
      return this.handleResponse(resp);
    } finally {
      clearTimeout(timer);
    }
  }

  private async post(
    url: string,
    body: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      return this.handleResponse(resp);
    } finally {
      clearTimeout(timer);
    }
  }

  private async handleResponse(resp: Response): Promise<Record<string, unknown>> {
    if (resp.status >= 400) {
      const text = await resp.text();
      throw new ApiError(resp.status, text);
    }
    return resp.json() as Promise<Record<string, unknown>>;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  getKeyPrefix(): string {
    return this.apiKey.substring(0, 12);
  }
}
