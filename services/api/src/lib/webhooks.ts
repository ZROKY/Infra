/**
 * Webhook outbound delivery — HMAC-signed payloads with retry + exponential backoff.
 */

import { createHmac, randomUUID } from 'node:crypto';

import type {
  WebhookConfig,
  WebhookDelivery,
  WebhookEventType,
} from './billing-types';

// ---------------------------------------------------------------------------
// In-memory stores (V1 — replaced with DB in production)
// ---------------------------------------------------------------------------

const webhookConfigs = new Map<string, WebhookConfig[]>(); // key: orgId
const deliveryLog: WebhookDelivery[] = [];

const RETRY_DELAYS = [1_000, 10_000, 60_000]; // 1s, 10s, 60s
const MAX_ATTEMPTS = 3;

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

export function registerWebhook(
  orgId: string,
  url: string,
  events: WebhookEventType[],
): WebhookConfig {
  const config: WebhookConfig = {
    id: `wh_${randomUUID().replace(/-/g, '')}`,
    orgId,
    url,
    secret: `whsec_${randomUUID().replace(/-/g, '')}`,
    events,
    active: true,
    createdAt: new Date().toISOString(),
  };

  const existing = webhookConfigs.get(orgId) || [];
  existing.push(config);
  webhookConfigs.set(orgId, existing);

  return config;
}

export function listWebhooks(orgId: string): WebhookConfig[] {
  return (webhookConfigs.get(orgId) || []).filter((w) => w.active);
}

export function deleteWebhook(orgId: string, webhookId: string): boolean {
  const configs = webhookConfigs.get(orgId);
  if (!configs) return false;

  const idx = configs.findIndex((w) => w.id === webhookId);
  if (idx === -1) return false;

  configs[idx]!.active = false;
  return true;
}

export function getDeliveryLog(
  webhookId: string,
  limit = 20,
): WebhookDelivery[] {
  return deliveryLog
    .filter((d) => d.webhookId === webhookId)
    .slice(-limit);
}

// ---------------------------------------------------------------------------
// Signing
// ---------------------------------------------------------------------------

export function signPayload(secret: string, body: string): string {
  return `sha256=${createHmac('sha256', secret).update(body).digest('hex')}`;
}

export function verifySignature(
  secret: string,
  body: string,
  signature: string,
): boolean {
  const expected = signPayload(secret, body);
  return expected === signature;
}

// ---------------------------------------------------------------------------
// Delivery
// ---------------------------------------------------------------------------

export async function dispatchEvent(
  orgId: string,
  eventType: WebhookEventType,
  data: Record<string, unknown>,
): Promise<void> {
  const configs = (webhookConfigs.get(orgId) || []).filter(
    (w) => w.active && w.events.includes(eventType),
  );

  const payload = {
    event_id: `evt_${randomUUID().replace(/-/g, '')}`,
    type: eventType,
    created_at: new Date().toISOString(),
    data,
  };

  for (const config of configs) {
    // Fire-and-forget with retries (non-blocking)
    deliverWithRetry(config, payload).catch(() => {
      // Swallow — delivery failures are logged, not thrown
    });
  }
}

async function deliverWithRetry(
  config: WebhookConfig,
  payload: Record<string, unknown>,
): Promise<void> {
  const body = JSON.stringify(payload);
  const signature = signPayload(config.secret, body);

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const delivery: WebhookDelivery = {
      id: `del_${randomUUID().replace(/-/g, '')}`,
      webhookId: config.id,
      eventType: payload.type as WebhookEventType,
      payload,
      statusCode: null,
      attempt,
      deliveredAt: null,
      error: null,
    };

    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 10_000);

      const resp = await fetch(config.url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-ZROKY-Signature': signature,
          'X-ZROKY-Event': payload.type as string,
          'User-Agent': 'ZROKY-Webhooks/1.0',
        },
        body,
        signal: controller.signal,
      });

      clearTimeout(timer);
      delivery.statusCode = resp.status;
      delivery.deliveredAt = new Date().toISOString();
      deliveryLog.push(delivery);

      // Success on 2xx
      if (resp.status >= 200 && resp.status < 300) {
        return;
      }

      // No retry on 4xx (except 429)
      if (resp.status >= 400 && resp.status < 500 && resp.status !== 429) {
        delivery.error = `Client error ${resp.status}`;
        return;
      }
    } catch (err) {
      delivery.error = err instanceof Error ? err.message : 'Unknown error';
      deliveryLog.push(delivery);
    }

    // Wait before retry (if not last attempt)
    if (attempt < MAX_ATTEMPTS) {
      const delay = RETRY_DELAYS[attempt - 1] || 60_000;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
}
