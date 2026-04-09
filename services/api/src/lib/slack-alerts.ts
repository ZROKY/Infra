/**
 * Slack Alert Service — Send ZROKY alerts to Slack channels via Incoming Webhooks.
 *
 * Supports:
 * - Incoming Webhook URL per org (no OAuth needed for V1)
 * - Rich Block Kit messages with severity colors
 * - Alert types: trust_score_drop, engine_threshold, safety_incident, anomaly
 * - Retry with exponential backoff (3 attempts)
 * - Fail-open: Slack delivery failures never block the platform
 */

import { randomUUID } from 'node:crypto';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export type AlertType =
  | 'trust_score_drop'
  | 'engine_threshold'
  | 'safety_incident'
  | 'anomaly';

export interface SlackConfig {
  id: string;
  orgId: string;
  webhookUrl: string;
  channel: string; // display name only (webhook is pre-bound to channel)
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AlertPayload {
  alertId: string;
  type: AlertType;
  severity: AlertSeverity;
  agentId: string;
  agentName: string;
  title: string;
  message: string;
  currentValue: number;
  threshold?: number;
  engine?: string;
  dashboardUrl?: string;
  timestamp: string;
}

export interface SlackDeliveryResult {
  success: boolean;
  alertId: string;
  slackConfigId: string;
  attempts: number;
  error?: string;
}

// ---------------------------------------------------------------------------
// In-memory store (V1 — replaced with DB in production)
// ---------------------------------------------------------------------------

const slackConfigs = new Map<string, SlackConfig[]>(); // key: orgId
const deliveryLog: SlackDeliveryResult[] = [];

const RETRY_DELAYS = [1_000, 5_000, 15_000]; // 1s, 5s, 15s
const MAX_ATTEMPTS = 3;

// ---------------------------------------------------------------------------
// Severity palette
// ---------------------------------------------------------------------------

const SEVERITY_COLORS: Record<AlertSeverity, string> = {
  low: '#36a64f',      // green
  medium: '#f2c744',   // amber
  high: '#e8590c',     // orange
  critical: '#d32f2f', // red
};

const SEVERITY_EMOJI: Record<AlertSeverity, string> = {
  low: ':large_green_circle:',
  medium: ':large_yellow_circle:',
  high: ':large_orange_circle:',
  critical: ':red_circle:',
};

// ---------------------------------------------------------------------------
// Configuration CRUD
// ---------------------------------------------------------------------------

export function addSlackConfig(
  orgId: string,
  webhookUrl: string,
  channel: string,
): SlackConfig {
  if (!webhookUrl.startsWith('https://hooks.slack.com/')) {
    throw new Error('Invalid Slack webhook URL');
  }

  const config: SlackConfig = {
    id: `slack_${randomUUID().replace(/-/g, '')}`,
    orgId,
    webhookUrl,
    channel,
    enabled: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  const existing = slackConfigs.get(orgId) || [];
  existing.push(config);
  slackConfigs.set(orgId, existing);

  return config;
}

export function listSlackConfigs(orgId: string): SlackConfig[] {
  return (slackConfigs.get(orgId) || []).filter((c) => c.enabled);
}

export function getSlackConfig(orgId: string, configId: string): SlackConfig | undefined {
  return (slackConfigs.get(orgId) || []).find((c) => c.id === configId);
}

export function updateSlackConfig(
  orgId: string,
  configId: string,
  updates: Partial<Pick<SlackConfig, 'webhookUrl' | 'channel' | 'enabled'>>,
): SlackConfig | null {
  const configs = slackConfigs.get(orgId);
  if (!configs) return null;

  const idx = configs.findIndex((c) => c.id === configId);
  if (idx === -1) return null;

  if (updates.webhookUrl && !updates.webhookUrl.startsWith('https://hooks.slack.com/')) {
    throw new Error('Invalid Slack webhook URL');
  }

  const config = configs[idx]!;
  Object.assign(config, updates, { updatedAt: new Date().toISOString() });
  return config;
}

export function deleteSlackConfig(orgId: string, configId: string): boolean {
  const configs = slackConfigs.get(orgId);
  if (!configs) return false;

  const idx = configs.findIndex((c) => c.id === configId);
  if (idx === -1) return false;

  configs[idx]!.enabled = false;
  configs[idx]!.updatedAt = new Date().toISOString();
  return true;
}

// ---------------------------------------------------------------------------
// Block Kit message builder
// ---------------------------------------------------------------------------

function buildSlackBlocks(alert: AlertPayload): Record<string, unknown> {
  const color = SEVERITY_COLORS[alert.severity];
  const emoji = SEVERITY_EMOJI[alert.severity];

  const fields: Array<{ type: string; text: string }> = [
    { type: 'mrkdwn', text: `*Agent:*\n${alert.agentName}` },
    { type: 'mrkdwn', text: `*Severity:*\n${emoji} ${alert.severity.toUpperCase()}` },
    { type: 'mrkdwn', text: `*Current Value:*\n${alert.currentValue}` },
  ];

  if (alert.threshold !== undefined) {
    fields.push({ type: 'mrkdwn', text: `*Threshold:*\n${alert.threshold}` });
  }
  if (alert.engine) {
    fields.push({ type: 'mrkdwn', text: `*Engine:*\n${alert.engine}` });
  }

  const blocks: Array<Record<string, unknown>> = [
    {
      type: 'header',
      text: { type: 'plain_text', text: `🚨 ${alert.title}`, emoji: true },
    },
    {
      type: 'section',
      text: { type: 'mrkdwn', text: alert.message },
    },
    {
      type: 'section',
      fields,
    },
    {
      type: 'context',
      elements: [
        {
          type: 'mrkdwn',
          text: `Alert ID: \`${alert.alertId}\` | ${alert.timestamp}`,
        },
      ],
    },
  ];

  if (alert.dashboardUrl) {
    blocks.push({
      type: 'actions',
      elements: [
        {
          type: 'button',
          text: { type: 'plain_text', text: 'View in Dashboard', emoji: true },
          url: alert.dashboardUrl,
          style: 'primary',
        },
      ],
    });
  }

  return {
    attachments: [
      {
        color,
        blocks,
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Delivery engine
// ---------------------------------------------------------------------------

async function sendToSlack(
  webhookUrl: string,
  payload: Record<string, unknown>,
): Promise<{ ok: boolean; status: number; body: string }> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10_000);

  try {
    const resp = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const body = await resp.text();
    return { ok: resp.ok, status: resp.status, body };
  } finally {
    clearTimeout(timer);
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function deliverAlert(
  orgId: string,
  alert: AlertPayload,
): Promise<SlackDeliveryResult[]> {
  const configs = listSlackConfigs(orgId);
  if (configs.length === 0) return [];

  const slackMessage = buildSlackBlocks(alert);
  const results: SlackDeliveryResult[] = [];

  for (const config of configs) {
    let lastError = '';
    let delivered = false;

    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
      try {
        const result = await sendToSlack(config.webhookUrl, slackMessage);
        if (result.ok) {
          delivered = true;
          results.push({
            success: true,
            alertId: alert.alertId,
            slackConfigId: config.id,
            attempts: attempt,
          });
          break;
        }
        lastError = `HTTP ${result.status}: ${result.body}`;
      } catch (err) {
        lastError = err instanceof Error ? err.message : String(err);
      }

      // Retry with backoff (skip sleep on last attempt)
      if (attempt < MAX_ATTEMPTS) {
        await sleep(RETRY_DELAYS[attempt - 1] || 5_000);
      }
    }

    if (!delivered) {
      const entry: SlackDeliveryResult = {
        success: false,
        alertId: alert.alertId,
        slackConfigId: config.id,
        attempts: MAX_ATTEMPTS,
        error: lastError,
      };
      results.push(entry);
    }

    deliveryLog.push(results[results.length - 1]!);
  }

  return results;
}

// ---------------------------------------------------------------------------
// Test alert (sends a sample message to verify webhook)
// ---------------------------------------------------------------------------

export async function sendTestAlert(
  orgId: string,
  configId: string,
): Promise<SlackDeliveryResult> {
  const config = getSlackConfig(orgId, configId);
  if (!config) {
    return { success: false, alertId: 'test', slackConfigId: configId, attempts: 0, error: 'Config not found' };
  }

  const testAlert: AlertPayload = {
    alertId: `test_${randomUUID().replace(/-/g, '').slice(0, 8)}`,
    type: 'trust_score_drop',
    severity: 'low',
    agentId: 'test-agent',
    agentName: 'Test Agent',
    title: 'ZROKY Test Alert',
    message: 'This is a test alert from ZROKY. If you see this, Slack integration is working! ✅',
    currentValue: 85,
    threshold: 70,
    dashboardUrl: 'https://app.zroky.ai',
    timestamp: new Date().toISOString(),
  };

  const results = await deliverAlert(orgId, testAlert);
  return results[0] || { success: false, alertId: testAlert.alertId, slackConfigId: configId, attempts: 0, error: 'No delivery result' };
}

// ---------------------------------------------------------------------------
// Delivery log
// ---------------------------------------------------------------------------

export function getSlackDeliveryLog(limit = 50): SlackDeliveryResult[] {
  return deliveryLog.slice(-limit);
}
