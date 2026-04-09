"""Latency monitor — P50/P95/P99 tracking with rolling window."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from ..config import settings
from ..models import LatencyMetrics, MonitorResult, MonitorType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class LatencyMonitor:
    """Track latency percentiles using a Redis-backed rolling window."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, latency_ms: int, client_id: str, agent_id: str
    ) -> tuple[MonitorResult, LatencyMetrics]:
        """Score latency against targets. Returns (result, metrics)."""
        self._record(client_id, agent_id, latency_ms)
        window = self._get_window(client_id, agent_id)

        if not window:
            window = [latency_ms]

        arr = np.array(window)
        p50 = int(np.percentile(arr, 50))
        p95 = int(np.percentile(arr, 95))
        p99 = int(np.percentile(arr, 99))

        metrics = LatencyMetrics(
            p50_ms=p50,
            p95_ms=p95,
            p99_ms=p99,
            avg_ms=int(np.mean(arr)),
            min_ms=int(np.min(arr)),
            max_ms=int(np.max(arr)),
        )

        # Score based on P95 vs target
        if p95 <= settings.latency_p50_target:
            score = 100.0
        elif p95 <= settings.latency_p95_target:
            ratio = (p95 - settings.latency_p50_target) / max(settings.latency_p95_target - settings.latency_p50_target, 1)
            score = 100.0 - ratio * 30.0  # 70-100
        elif p95 <= settings.latency_p99_target:
            ratio = (p95 - settings.latency_p95_target) / max(settings.latency_p99_target - settings.latency_p95_target, 1)
            score = 70.0 - ratio * 40.0  # 30-70
        else:
            score = max(0.0, 30.0 - (p95 - settings.latency_p99_target) / 100.0)

        threshold_exceeded = p95 > settings.latency_p95_target

        result = MonitorResult(
            monitor_type=MonitorType.latency,
            score=round(score, 1),
            confidence=min(1.0, len(window) / 20.0),
            threshold_exceeded=threshold_exceeded,
            details={
                "p50_ms": p50, "p95_ms": p95, "p99_ms": p99,
                "p95_target": settings.latency_p95_target,
            },
        )
        return result, metrics

    def _record(self, client_id: str, agent_id: str, latency_ms: int) -> None:
        if not self._redis:
            return
        try:
            key = f"latency_window:{client_id}:{agent_id}"
            self._redis.rpush(key, str(latency_ms))
            self._redis.ltrim(key, -500, -1)  # Keep last 500
            self._redis.expire(key, 3600)
        except Exception:
            logger.warning("Failed to record latency")

    def _get_window(self, client_id: str, agent_id: str) -> list[int]:
        if not self._redis:
            return []
        try:
            key = f"latency_window:{client_id}:{agent_id}"
            raw = self._redis.lrange(key, 0, -1)
            return [int(v) for v in raw] if raw else []
        except Exception:
            logger.warning("Failed to get latency window")
        return []
