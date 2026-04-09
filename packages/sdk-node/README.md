# ZROKY Node.js SDK

AI Trust Infrastructure — Node.js/TypeScript SDK for monitoring and scoring AI agent interactions.

## Installation

```bash
npm install @zroky/sdk
```

## Quick Start

```typescript
import { ZROKYMonitor } from '@zroky/sdk';

const monitor = new ZROKYMonitor({
  apiKey: 'zk_ingest_...',
  agentId: 'agent_abc123',
});

// Track an AI interaction (returns immediately, sent async)
monitor.track(prompt, response, {
  model: 'gpt-4',
  sessionId: 'sess_123',
});

// Close when done (flushes remaining events)
await monitor.close();
```

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `apiKey` | Required | Your ZROKY ingest API key |
| `agentId` | Required | Unique identifier for your AI agent |
| `failOpen` | `true` | If true, errors are swallowed (AI keeps working) |
| `batchSize` | `50` | Events per batch |
| `flushInterval` | `5000` | Milliseconds between auto-flushes |
| `maxQueueSize` | `10000` | Max events in local queue |

## Design Principles

- **Fail-open**: ZROKY never blocks your AI pipeline
- **Async batching**: Events are queued and sent in background
- **Circuit breaker**: Auto-disables after 5 consecutive failures, retries after 60s
- **Tiny footprint**: < 200KB, zero runtime dependencies
- **Native fetch**: Uses Node.js built-in fetch (18+)
