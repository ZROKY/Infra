package zroky

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestNewClient_RequiresAPIKey(t *testing.T) {
	_, err := NewClient(ClientConfig{})
	if err == nil {
		t.Fatal("expected error for empty APIKey")
	}
}

func TestNewClient_Defaults(t *testing.T) {
	c, err := NewClient(ClientConfig{APIKey: "zk_test_123"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if c.baseURL != defaultBaseURL {
		t.Errorf("expected baseURL %q, got %q", defaultBaseURL, c.baseURL)
	}
	if c.ingestURL != defaultIngestURL {
		t.Errorf("expected ingestURL %q, got %q", defaultIngestURL, c.ingestURL)
	}
}

func TestSendEvent(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if r.URL.Path != "/v1/events" {
			t.Errorf("expected /v1/events, got %s", r.URL.Path)
		}
		if r.Header.Get("Authorization") != "Bearer zk_test_123" {
			t.Error("missing or wrong Authorization header")
		}

		var evt Event
		json.NewDecoder(r.Body).Decode(&evt)
		if evt.AgentID != "agent_abc" {
			t.Errorf("expected agent_id 'agent_abc', got %q", evt.AgentID)
		}

		w.WriteHeader(200)
		w.Write([]byte(`{"status":"ok"}`))
	}))
	defer server.Close()

	c, _ := NewClient(ClientConfig{
		APIKey:    "zk_test_123",
		IngestURL: server.URL,
	})

	err := c.SendEvent(Event{
		AgentID:  "agent_abc",
		Prompt:   "hello",
		Response: "world",
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestSendBatch(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/events/batch" {
			t.Errorf("expected /v1/events/batch, got %s", r.URL.Path)
		}
		w.WriteHeader(200)
		w.Write([]byte(`{"accepted":2}`))
	}))
	defer server.Close()

	c, _ := NewClient(ClientConfig{
		APIKey:    "zk_test_123",
		IngestURL: server.URL,
	})

	err := c.SendBatch([]Event{
		{AgentID: "a", Prompt: "p1", Response: "r1"},
		{AgentID: "a", Prompt: "p2", Response: "r2"},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestGetTrustScore(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if r.URL.Path != "/v1/trust-score/agent_abc" {
			t.Errorf("expected /v1/trust-score/agent_abc, got %s", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(TrustScore{
			Score:  85.0,
			Status: "trusted",
			AgentID: "agent_abc",
		})
	}))
	defer server.Close()

	c, _ := NewClient(ClientConfig{
		APIKey:  "zk_test_123",
		BaseURL: server.URL,
	})

	score, err := c.GetTrustScore("agent_abc")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if score.Score != 85.0 {
		t.Errorf("expected score 85, got %f", score.Score)
	}
	if score.Status != "trusted" {
		t.Errorf("expected status 'trusted', got %q", score.Status)
	}
}

func TestGetTrustScore_Error(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(401)
		w.Write([]byte("Unauthorized"))
	}))
	defer server.Close()

	c, _ := NewClient(ClientConfig{
		APIKey:  "zk_test_123",
		BaseURL: server.URL,
	})

	_, err := c.GetTrustScore("agent_abc")
	if err == nil {
		t.Fatal("expected error for 401")
	}
}
