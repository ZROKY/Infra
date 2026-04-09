// Package zroky provides the ZROKY Go SDK for AI Trust Infrastructure.
//
// This is a stub for V1 — basic event sending and score querying.
// Full implementation (batching, circuit breaker) is planned for V2.
package zroky

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Version is the current SDK version.
const Version = "0.1.0"

const (
	defaultBaseURL   = "https://api.zroky.ai"
	defaultIngestURL = "https://ingest.zroky.ai"
	defaultTimeout   = 10 * time.Second
)

// ClientConfig holds configuration for the ZROKY client.
type ClientConfig struct {
	APIKey    string
	BaseURL   string
	IngestURL string
	Timeout   time.Duration
}

// Client is the low-level HTTP client for the ZROKY API.
type Client struct {
	apiKey    string
	baseURL   string
	ingestURL string
	http      *http.Client
}

// NewClient creates a new ZROKY API client.
func NewClient(cfg ClientConfig) (*Client, error) {
	if cfg.APIKey == "" {
		return nil, fmt.Errorf("zroky: APIKey is required")
	}
	if cfg.BaseURL == "" {
		cfg.BaseURL = defaultBaseURL
	}
	if cfg.IngestURL == "" {
		cfg.IngestURL = defaultIngestURL
	}
	if cfg.Timeout == 0 {
		cfg.Timeout = defaultTimeout
	}

	return &Client{
		apiKey:    cfg.APIKey,
		baseURL:   cfg.BaseURL,
		ingestURL: cfg.IngestURL,
		http:      &http.Client{Timeout: cfg.Timeout},
	}, nil
}

// Event represents an AI interaction event to be sent to ZROKY.
type Event struct {
	AgentID   string                 `json:"agent_id"`
	Prompt    string                 `json:"prompt"`
	Response  string                 `json:"response"`
	Model     string                 `json:"model,omitempty"`
	SessionID string                 `json:"session_id,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
	Timestamp float64                `json:"timestamp"`
}

// TrustScore represents the ZROKY Trust Score response.
type TrustScore struct {
	Score       float64                `json:"score"`
	Status      string                 `json:"status"`
	EngineScores map[string]float64    `json:"engine_scores"`
	AgentID     string                 `json:"agent_id"`
}

// SendEvent sends a single event to the ZROKY ingestion endpoint.
func (c *Client) SendEvent(event Event) error {
	if event.Timestamp == 0 {
		event.Timestamp = float64(time.Now().UnixMilli()) / 1000.0
	}

	body, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("zroky: marshal event: %w", err)
	}

	url := fmt.Sprintf("%s/v1/events", c.ingestURL)
	return c.doPost(url, body)
}

// SendBatch sends a batch of events to the ZROKY ingestion endpoint.
func (c *Client) SendBatch(events []Event) error {
	now := float64(time.Now().UnixMilli()) / 1000.0
	for i := range events {
		if events[i].Timestamp == 0 {
			events[i].Timestamp = now
		}
	}

	payload := struct {
		Events []Event `json:"events"`
	}{Events: events}

	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("zroky: marshal batch: %w", err)
	}

	url := fmt.Sprintf("%s/v1/events/batch", c.ingestURL)
	return c.doPost(url, body)
}

// GetTrustScore fetches the current Trust Score for an agent.
func (c *Client) GetTrustScore(agentID string) (*TrustScore, error) {
	url := fmt.Sprintf("%s/v1/trust-score/%s", c.baseURL, agentID)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("zroky: create request: %w", err)
	}
	c.setHeaders(req)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("zroky: request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("zroky: API %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var score TrustScore
	if err := json.NewDecoder(resp.Body).Decode(&score); err != nil {
		return nil, fmt.Errorf("zroky: decode response: %w", err)
	}

	return &score, nil
}

// -- Internal helpers -------------------------------------------------------

func (c *Client) doPost(url string, body []byte) error {
	req, err := http.NewRequest("POST", url, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("zroky: create request: %w", err)
	}
	c.setHeaders(req)

	resp, err := c.http.Do(req)
	if err != nil {
		return fmt.Errorf("zroky: request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("zroky: API %d: %s", resp.StatusCode, string(bodyBytes))
	}

	return nil
}

func (c *Client) setHeaders(req *http.Request) {
	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("User-Agent", "zroky-go/"+Version)
	req.Header.Set("Content-Type", "application/json")
}
