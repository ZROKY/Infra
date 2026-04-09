"""ZROKY Monitor — high-level async event tracker with batching and fail-open."""

from __future__ import annotations

import atexit
import logging
import threading
import time
from typing import Any

from zroky.client import ZrokyClient

logger = logging.getLogger("zroky")

_DEFAULT_BATCH_SIZE = 50
_DEFAULT_FLUSH_INTERVAL = 5.0
_DEFAULT_MAX_QUEUE = 10_000
_CIRCUIT_BREAKER_THRESHOLD = 5
_CIRCUIT_BREAKER_COOLDOWN = 60.0


class ZROKYMonitor:
    """High-level monitor that batches events and sends them asynchronously.

    Fail-open by default — if ZROKY is unreachable, client AI keeps working.
    Events are queued locally and sent in background.
    """

    def __init__(
        self,
        api_key: str,
        agent_id: str,
        *,
        fail_open: bool = True,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        flush_interval: float = _DEFAULT_FLUSH_INTERVAL,
        max_queue_size: int = _DEFAULT_MAX_QUEUE,
        base_url: str = "https://api.zroky.ai",
        ingest_url: str = "https://ingest.zroky.ai",
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if not agent_id:
            raise ValueError("agent_id is required")

        self._agent_id = agent_id
        self._fail_open = fail_open
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._max_queue_size = max_queue_size

        self._client = ZrokyClient(api_key=api_key, base_url=base_url, ingest_url=ingest_url)
        self._queue: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._closed = False

        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0

        # Background flush thread
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

        atexit.register(self.close)

    def track(
        self,
        prompt: str,
        response: str,
        *,
        model: str = "",
        session_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Track an AI interaction event. Returns immediately (< 1ms)."""
        if self._closed:
            raise RuntimeError("Monitor is closed")

        event = {
            "agent_id": self._agent_id,
            "prompt": prompt,
            "response": response,
            "model": model,
            "session_id": session_id,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }

        with self._lock:
            if len(self._queue) >= self._max_queue_size:
                if self._fail_open:
                    logger.warning("ZROKY queue full (%d), dropping event", self._max_queue_size)
                    return {"status": "dropped", "reason": "queue_full"}
                raise RuntimeError(f"ZROKY event queue full ({self._max_queue_size})")
            self._queue.append(event)

        return {"status": "queued"}

    def flush(self) -> int:
        """Flush all queued events immediately. Returns count of events sent."""
        with self._lock:
            if not self._queue:
                return 0
            batch = self._queue[: self._batch_size]
            self._queue = self._queue[self._batch_size :]

        return self._send_batch(batch)

    def close(self) -> None:
        """Flush remaining events and close the monitor."""
        if self._closed:
            return
        self._closed = True

        # Flush all remaining
        while True:
            with self._lock:
                if not self._queue:
                    break
                batch = self._queue[: self._batch_size]
                self._queue = self._queue[self._batch_size :]
            self._send_batch(batch)

        self._client.close()

    # -- Internal ------------------------------------------------------------

    def _flush_loop(self) -> None:
        """Background thread that periodically flushes the queue."""
        while not self._closed:
            time.sleep(self._flush_interval)
            try:
                while True:
                    with self._lock:
                        if not self._queue:
                            break
                        batch = self._queue[: self._batch_size]
                        self._queue = self._queue[self._batch_size :]
                    self._send_batch(batch)
            except Exception:
                logger.exception("ZROKY flush error")

    def _send_batch(self, events: list[dict[str, Any]]) -> int:
        """Send a batch of events, respecting the circuit breaker."""
        if not events:
            return 0

        # Circuit breaker check
        if self._circuit_open_until > time.time():
            logger.debug("ZROKY circuit open, requeueing %d events", len(events))
            with self._lock:
                self._queue = events + self._queue
            return 0

        try:
            if len(events) == 1:
                self._client.send_event(events[0])
            else:
                self._client.send_batch(events)

            self._consecutive_failures = 0
            return len(events)

        except Exception:
            self._consecutive_failures += 1
            if self._consecutive_failures >= _CIRCUIT_BREAKER_THRESHOLD:
                self._circuit_open_until = time.time() + _CIRCUIT_BREAKER_COOLDOWN
                logger.warning(
                    "ZROKY circuit breaker opened after %d failures, cooldown %ds",
                    _CIRCUIT_BREAKER_THRESHOLD,
                    _CIRCUIT_BREAKER_COOLDOWN,
                )

            if self._fail_open:
                logger.warning("ZROKY send failed, requeueing %d events", len(events))
                with self._lock:
                    self._queue = events + self._queue
                return 0
            raise

    @property
    def queue_size(self) -> int:
        """Current number of events in the queue."""
        with self._lock:
            return len(self._queue)

    @property
    def is_circuit_open(self) -> bool:
        """Whether the circuit breaker is currently open."""
        return self._circuit_open_until > time.time()
