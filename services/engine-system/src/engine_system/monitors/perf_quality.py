"""Performance-quality correlation monitor — Pearson r coefficient tracking."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from ..config import settings
from ..models import MonitorResult, MonitorType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class PerfQualityMonitor:
    """Track Pearson r between latency and quality scores to detect inverse correlation."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, latency_ms: int, quality_score: float, client_id: str, agent_id: str
    ) -> MonitorResult:
        """Compute correlation between latency and quality."""
        self._record(client_id, agent_id, latency_ms, quality_score)
        pairs = self._get_pairs(client_id, agent_id)

        if len(pairs) < 10:
            return MonitorResult(
                monitor_type=MonitorType.performance_quality_correlation,
                score=85.0,
                confidence=0.3,
                details={"reason": "insufficient_data", "sample_count": len(pairs)},
            )

        latencies = np.array([p[0] for p in pairs])
        qualities = np.array([p[1] for p in pairs])

        # Pearson r
        if np.std(latencies) == 0 or np.std(qualities) == 0:
            r = 0.0
        else:
            r = float(np.corrcoef(latencies, qualities)[0, 1])

        # Negative r means higher latency → lower quality (bad)
        # r = 0 → no correlation (neutral, score ~80)
        # r > 0 → higher latency sometimes = better quality (acceptable)
        if r >= 0:
            score = 90.0 + r * 10  # 90-100
        elif r >= settings.correlation_alert_threshold:
            ratio = abs(r) / abs(settings.correlation_alert_threshold)
            score = 90.0 - ratio * 30.0  # 60-90
        else:
            score = max(0.0, 60.0 - (abs(r) - abs(settings.correlation_alert_threshold)) * 100)

        return MonitorResult(
            monitor_type=MonitorType.performance_quality_correlation,
            score=round(score, 1),
            confidence=min(1.0, len(pairs) / 50.0),
            threshold_exceeded=r < settings.correlation_alert_threshold,
            details={
                "pearson_r": round(r, 4),
                "sample_count": len(pairs),
                "alert_threshold": settings.correlation_alert_threshold,
            },
        )

    def _record(self, client_id: str, agent_id: str, latency_ms: int, quality: float) -> None:
        if not self._redis:
            return
        try:
            import json
            key = f"perf_quality_pairs:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            pairs = json.loads(raw) if raw else []
            pairs.append([latency_ms, quality])
            pairs = pairs[-200:]  # Keep last 200
            self._redis.set(key, json.dumps(pairs), ex=86400)
        except Exception:
            logger.warning("Failed to record perf-quality pair")

    def _get_pairs(self, client_id: str, agent_id: str) -> list[list[float]]:
        if not self._redis:
            return []
        try:
            import json
            key = f"perf_quality_pairs:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            return json.loads(raw) if raw else []
        except Exception:
            logger.warning("Failed to get perf-quality pairs")
        return []
