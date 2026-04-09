"""Uptime monitor — availability tracking via health check results."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..config import settings
from ..models import MonitorResult, MonitorType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class UptimeMonitor:
    """Track uptime percentage using health check pass/fail counters."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, is_error: bool, client_id: str, agent_id: str
    ) -> MonitorResult:
        """Record health check and compute uptime percentage."""
        self._record(client_id, agent_id, not is_error)
        total, successes = self._get_counts(client_id, agent_id)

        if total == 0:
            total, successes = 1, 0 if is_error else 1

        uptime_pct = (successes / total) * 100

        # Score: 100% uptime → 100, below target → degrades
        if uptime_pct >= settings.uptime_target_pct:
            score = 100.0
        elif uptime_pct >= 99.0:
            ratio = (settings.uptime_target_pct - uptime_pct) / max(settings.uptime_target_pct - 99.0, 0.01)
            score = 100.0 - ratio * 30.0  # 70-100
        elif uptime_pct >= 95.0:
            score = 70.0 - (99.0 - uptime_pct) * 7.5  # 40-70
        else:
            score = max(0.0, 40.0 - (95.0 - uptime_pct) * 2.0)

        return MonitorResult(
            monitor_type=MonitorType.uptime,
            score=round(score, 1),
            confidence=min(1.0, total / 50.0),
            threshold_exceeded=uptime_pct < settings.uptime_target_pct,
            details={
                "uptime_pct": round(uptime_pct, 3),
                "total_checks": total,
                "successful_checks": successes,
                "target_pct": settings.uptime_target_pct,
            },
        )

    def _record(self, client_id: str, agent_id: str, success: bool) -> None:
        if not self._redis:
            return
        try:
            total_key = f"uptime_total:{client_id}:{agent_id}"
            success_key = f"uptime_success:{client_id}:{agent_id}"
            pipe = self._redis.pipeline()
            pipe.incr(total_key)
            if success:
                pipe.incr(success_key)
            pipe.expire(total_key, 86400)
            pipe.expire(success_key, 86400)
            pipe.execute()
        except Exception:
            logger.warning("Failed to record uptime data")

    def _get_counts(self, client_id: str, agent_id: str) -> tuple[int, int]:
        if not self._redis:
            return 0, 0
        try:
            total_key = f"uptime_total:{client_id}:{agent_id}"
            success_key = f"uptime_success:{client_id}:{agent_id}"
            total = self._redis.get(total_key)
            successes = self._redis.get(success_key)
            return int(total or 0), int(successes or 0)
        except Exception:
            logger.warning("Failed to get uptime counts")
        return 0, 0
