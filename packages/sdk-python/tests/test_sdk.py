"""Tests for the ZROKY Python SDK."""

from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from zroky import __version__
from zroky.client import ApiError, ZrokyClient
from zroky.monitor import ZROKYMonitor


# ===========================================================================
# Client tests
# ===========================================================================


class TestZrokyClient:
    def test_rejects_empty_api_key(self) -> None:
        with pytest.raises(ValueError, match="api_key"):
            ZrokyClient(api_key="")

    def test_default_urls(self) -> None:
        client = ZrokyClient(api_key="zk_test_123")
        assert client._base_url == "https://api.zroky.ai"
        assert client._ingest_url == "https://ingest.zroky.ai"
        client.close()

    def test_send_event(self) -> None:
        client = ZrokyClient(api_key="zk_test_123")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok"}

        with patch.object(client._http, "post", return_value=mock_resp):
            result = client.send_event({"agent_id": "test", "prompt": "hi"})
            assert result["status"] == "ok"

        client.close()

    def test_send_batch(self) -> None:
        client = ZrokyClient(api_key="zk_test_123")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"accepted": 2}

        events = [{"prompt": "a"}, {"prompt": "b"}]
        with patch.object(client._http, "post", return_value=mock_resp):
            result = client.send_batch(events)
            assert result["accepted"] == 2

        client.close()

    def test_get_trust_score(self) -> None:
        client = ZrokyClient(api_key="zk_test_123")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"score": 85, "status": "trusted"}

        with patch.object(client._http, "get", return_value=mock_resp):
            result = client.get_trust_score("agent_abc")
            assert result["score"] == 85

        client.close()

    def test_api_error_on_4xx(self) -> None:
        client = ZrokyClient(api_key="zk_test_123")
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"

        with patch.object(client._http, "get", return_value=mock_resp):
            with pytest.raises(ApiError, match="401"):
                client.get_trust_score("agent_abc")

        client.close()

    def test_context_manager(self) -> None:
        with ZrokyClient(api_key="zk_test_123") as client:
            assert client._api_key == "zk_test_123"

    def test_user_agent(self) -> None:
        client = ZrokyClient(api_key="zk_test_123")
        assert f"zroky-python/{__version__}" in client._headers["User-Agent"]
        client.close()


# ===========================================================================
# Monitor tests
# ===========================================================================


class TestZROKYMonitor:
    def test_rejects_empty_api_key(self) -> None:
        with pytest.raises(ValueError, match="api_key"):
            ZROKYMonitor(api_key="", agent_id="test")

    def test_rejects_empty_agent_id(self) -> None:
        with pytest.raises(ValueError, match="agent_id"):
            ZROKYMonitor(api_key="zk_test_123", agent_id="")

    def test_track_queues_event(self) -> None:
        monitor = ZROKYMonitor(api_key="zk_test_123", agent_id="test")
        result = monitor.track(prompt="hello", response="world")
        assert result["status"] == "queued"
        assert monitor.queue_size == 1
        monitor._closed = True

    def test_track_after_close_raises(self) -> None:
        monitor = ZROKYMonitor(api_key="zk_test_123", agent_id="test")
        monitor._closed = True
        with pytest.raises(RuntimeError, match="closed"):
            monitor.track(prompt="hello", response="world")

    def test_queue_full_drops_in_fail_open(self) -> None:
        monitor = ZROKYMonitor(
            api_key="zk_test_123", agent_id="test", fail_open=True, max_queue_size=2
        )
        monitor.track(prompt="a", response="b")
        monitor.track(prompt="c", response="d")
        result = monitor.track(prompt="e", response="f")
        assert result["status"] == "dropped"
        monitor._closed = True

    def test_queue_full_raises_in_fail_closed(self) -> None:
        monitor = ZROKYMonitor(
            api_key="zk_test_123", agent_id="test", fail_open=False, max_queue_size=1
        )
        monitor.track(prompt="a", response="b")
        with pytest.raises(RuntimeError, match="queue full"):
            monitor.track(prompt="c", response="d")
        monitor._closed = True

    def test_flush_sends_batch(self) -> None:
        monitor = ZROKYMonitor(api_key="zk_test_123", agent_id="test")
        monitor.track(prompt="hello", response="world")

        with patch.object(monitor._client, "send_event", return_value={"status": "ok"}):
            count = monitor.flush()
            assert count == 1
            assert monitor.queue_size == 0

        monitor._closed = True

    def test_circuit_breaker_opens(self) -> None:
        monitor = ZROKYMonitor(api_key="zk_test_123", agent_id="test")
        # Simulate 5 consecutive failures
        for _ in range(5):
            monitor.track(prompt="hello", response="world")
            with patch.object(
                monitor._client, "send_event", side_effect=Exception("network error")
            ):
                monitor.flush()

        assert monitor.is_circuit_open is True
        monitor._closed = True

    def test_event_includes_metadata(self) -> None:
        monitor = ZROKYMonitor(api_key="zk_test_123", agent_id="test")
        monitor.track(
            prompt="hello",
            response="world",
            model="gpt-4",
            session_id="sess_123",
            metadata={"foo": "bar"},
        )

        event = monitor._queue[0]
        assert event["model"] == "gpt-4"
        assert event["session_id"] == "sess_123"
        assert event["metadata"]["foo"] == "bar"
        assert "timestamp" in event
        monitor._closed = True
