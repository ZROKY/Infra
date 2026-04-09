# ZROKY Python SDK

AI Trust Infrastructure — Python SDK for monitoring and scoring AI agent interactions.

## Installation

```bash
pip install zroky
```

## Quick Start

```python
from zroky import ZROKYMonitor

monitor = ZROKYMonitor(
    api_key="zk_ingest_...",
    agent_id="agent_abc123"
)

# Track an AI interaction (returns immediately, sent async)
monitor.track(
    prompt=user_input,
    response=ai_output,
    model="gpt-4",
    session_id="sess_123"
)

# Close when done (flushes remaining events)
monitor.close()
```

## LangChain Integration

```python
from zroky.integrations.langchain import ZROKYCallbackHandler

handler = ZROKYCallbackHandler(
    api_key="zk_ingest_...",
    agent_id="agent_abc123"
)

result = chain.invoke(input, config={"callbacks": [handler]})
```

## LangGraph Integration

```python
from zroky.integrations.langgraph import ZROKYGraph

monitored = ZROKYGraph(
    graph,
    api_key="zk_ingest_...",
    agent_id="agent_abc123"
)

result = monitored.invoke(input)
```

## LiteLLM Integration

```python
import litellm
from zroky.integrations.litellm import ZROKYLiteLLMCallback

callback = ZROKYLiteLLMCallback(
    api_key="zk_ingest_...",
    agent_id="agent_abc123"
)

litellm.success_callback = [callback.on_success]
litellm.failure_callback = [callback.on_failure]
```

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `api_key` | Required | Your ZROKY ingest API key |
| `agent_id` | Required | Unique identifier for your AI agent |
| `fail_open` | `True` | If True, errors are swallowed (AI keeps working) |
| `batch_size` | `50` | Events per batch |
| `flush_interval` | `5.0` | Seconds between auto-flushes |
| `max_queue_size` | `10000` | Max events in local queue |

## Design Principles

- **Fail-open**: ZROKY never blocks your AI pipeline
- **Async batching**: Events are queued and sent in background
- **Circuit breaker**: Auto-disables after 5 consecutive failures, retries after 60s
- **Tiny footprint**: < 500KB, only httpx + pydantic deps
