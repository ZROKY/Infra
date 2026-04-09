"""Throughput monitor — RPS and capacity utilization tracking."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from ..config import settings
from ..models import MonitorResult, MonitorType, ThroughputMetrics

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)

# Assumed max RPS (auto-calibrated from peak)
DEFAULT_MAX_RPS = 100.0


class ThroughputMonitor:
    """Track requests per second and capacity utilization."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, client_id: str, agent_id: str
    ) -> tuple[MonitorResult, ThroughputMetrics]:
        """Record request and compute RPS / utilization. Returns (result, metrics)."""
        self._record_request(client_id, agent_id)
        current_rps = self._get_rps(client_id, agent_id)
        peak_rps = self._get_peak_rps(client_id, agent_id)

        # Auto-calibrate max from peak (with floor)
        max_rps = max(peak_rps * 1.2, DEFAULT_MAX_RPS)
        utilization = (current_rps / max_rps) * 100

        metrics = ThroughputMetrics(
            current_rps=round(current_rps, 2),
            capacity_utilization_pct=round(utilization, 1),
            peak_rps_today=round(peak_rps, 2),
        )

        # Score: under 50% → 100, over 80% → degraded, over 95% → critical
        if utilization <= 50:
            score = 100.0
        elif utilization <= settings.throughput_capacity_alert_pct:
            ratio = (utilization - 50) / max(settings.throughput_capacity_alert_pct - 50, 1)
            score = 100.0 - ratio * 20.0
        elif utilization <= 95:
            ratio = (utilization - settings.throughput_capacity_alert_pct) / (95 - settings.throughput_capacity_alert_pct)
            score = 80.0 - ratio * 50.0
        else:
            score = max(0.0, 30.0 - (utilization - 95) * 6.0)

        return MonitorResult(
            monitor_type=MonitorType.throughput,
            score=round(score, 1),
            confidence=0.8,
            threshold_exceeded=utilization > settings.throughput_capacity_alert_pct,
            details={
                "current_rps": round(current_rps, 2),
                "peak_rps": round(peak_rps, 2),
                "utilization_pct": round(utilization, 1),
                "alert_threshold_pct": settings.throughput_capacity_alert_pct,
            },
        ), metrics

    def _record_request(self, client_id: str, agent_id: str) -> None:
        if not self._redis:
            return
        try:
            now_sec = int(time.time())
            key = f"throughput:{client_id}:{agent_id}:{now_sec}"
            pipe = self._redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, 120)  # Keep 2 minutes of second-level counters
            pipe.execute()
        except Exception:
            logger.warning("Failed to record throughput")

    def _get_rps(self, client_id: str, agent_id: str) -> float:
        if not self._redis:
            return 0.0
        try:
            now_sec = int(time.time())
            # Average over last 10 seconds
            keys = [f"throughput:{client_id}:{agent_id}:{now_sec - i}" for i in range(10)]
            values = self._redis.mget(keys)
            total = sum(int(v) for v in values if v)
            return total / 10.0
        except Exception:
            logger.warning("Failed to get RPS")
        return 0.0

    def _get_peak_rps(self, client_id: str, agent_id: str) -> float:
        if not self._redis:
            return 0.0
        try:
            key = f"throughput_peak:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            current_rps = self._get_rps(client_id, agent_id)
            peak = float(raw) if raw else 0.0
            if current_rps > peak:
                self._redis.set(key, str(current_rps), ex=86400)
                return current_rps
            return peak
        except Exception:
            logger.warning("Failed to get peak RPS")
        return 0.0
