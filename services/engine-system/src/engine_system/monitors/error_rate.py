"""Error rate monitor — HTTP error tracking with rolling window."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..config import settings
from ..models import MonitorResult, MonitorType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class ErrorRateMonitor:
    """Track error rates across 429/500/503/timeout errors."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, status_code: int, is_error: bool, client_id: str, agent_id: str
    ) -> MonitorResult:
        """Compute rolling error rate and score."""
        self._record(client_id, agent_id, is_error)
        total, errors = self._get_counts(client_id, agent_id)

        if total == 0:
            total, errors = 1, int(is_error)

        error_rate = (errors / total) * 100

        # Score: 0% errors → 100, ≥10% errors → 0
        if error_rate <= 1.0:
            score = 100.0
        elif error_rate <= settings.error_rate_alert_pct:
            ratio = (error_rate - 1.0) / max(settings.error_rate_alert_pct - 1.0, 1)
            score = 100.0 - ratio * 50.0  # 50-100
        else:
            score = max(0.0, 50.0 - (error_rate - settings.error_rate_alert_pct) * 5.0)

        return MonitorResult(
            monitor_type=MonitorType.error_rate,
            score=round(score, 1),
            confidence=min(1.0, total / 20.0),
            threshold_exceeded=error_rate > settings.error_rate_alert_pct,
            details={
                "error_rate_pct": round(error_rate, 2),
                "total_requests": total,
                "total_errors": errors,
                "status_code": status_code,
                "alert_threshold_pct": settings.error_rate_alert_pct,
            },
        )

    def _record(self, client_id: str, agent_id: str, is_error: bool) -> None:
        if not self._redis:
            return
        try:
            total_key = f"error_total:{client_id}:{agent_id}"
            error_key = f"error_count:{client_id}:{agent_id}"
            pipe = self._redis.pipeline()
            pipe.incr(total_key)
            if is_error:
                pipe.incr(error_key)
            pipe.expire(total_key, 3600)
            pipe.expire(error_key, 3600)
            pipe.execute()
        except Exception:
            logger.warning("Failed to record error data")

    def _get_counts(self, client_id: str, agent_id: str) -> tuple[int, int]:
        if not self._redis:
            return 0, 0
        try:
            total_key = f"error_total:{client_id}:{agent_id}"
            error_key = f"error_count:{client_id}:{agent_id}"
            total = self._redis.get(total_key)
            errors = self._redis.get(error_key)
            return int(total or 0), int(errors or 0)
        except Exception:
            logger.warning("Failed to get error counts")
        return 0, 0
