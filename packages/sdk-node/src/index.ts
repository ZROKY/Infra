/**
 * ZROKY Node.js SDK — AI Trust Infrastructure
 */

export const VERSION = '0.1.0';

export interface ZrokyClientConfig {
  apiKey: string;
  baseUrl?: string;
}

export class ZrokyClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;

  constructor(config: ZrokyClientConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || 'https://api.zroky.ai';
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }
}
