# ZROKY Go SDK

AI Trust Infrastructure — Go SDK for monitoring and scoring AI agent interactions.

> **V1 Stub**: This SDK provides basic event sending and Trust Score querying.
> Full batching + circuit breaker support is planned for V2.

## Installation

```bash
go get github.com/zroky/sdk-go
```

## Quick Start

```go
package main

import (
    "log"
    zroky "github.com/zroky/sdk-go"
)

func main() {
    client, err := zroky.NewClient(zroky.ClientConfig{
        APIKey: "zk_ingest_...",
    })
    if err != nil {
        log.Fatal(err)
    }

    // Send an event
    err = client.SendEvent(zroky.Event{
        AgentID:  "agent_abc123",
        Prompt:   userInput,
        Response: aiOutput,
        Model:    "gpt-4",
    })

    // Query Trust Score
    score, err := client.GetTrustScore("agent_abc123")
    if err == nil {
        log.Printf("Trust Score: %.1f (%s)", score.Score, score.Status)
    }
}
```
