"""Coverage calculator — events_received_24h / expected_daily_events × 100.

Expected daily events = rolling 7-day average × 0.80 (allows 20% variance).
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from .config import settings
from .models import CoverageBand, CoverageInfo

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class CoverageCalculator:
    """Compute coverage score from event volume."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    def compute(
        self, events_received_24h: int, expected_daily_events: int, client_id: str, agent_id: str
    ) -> CoverageInfo:
        """Compute coverage score from event counts."""
        # Update rolling average
        self._record_daily_count(client_id, agent_id, events_received_24h)

        # If no expectation provided, derive from 7-day rolling average
        if expected_daily_events <= 0:
            expected_daily_events = self._get_expected_daily(client_id, agent_id)

        if expected_daily_events <= 0:
            # No history — be lenient
            return CoverageInfo(
                score=50.0,
                band=CoverageBand.partial_coverage,
                events_received_24h=events_received_24h,
                expected_daily_events=0,
            )

        raw_score = (events_received_24h / expected_daily_events) * 100
        score = min(100.0, raw_score)  # Cap at 100

        if score >= 80:
            band = CoverageBand.full_coverage
        elif score >= 50:
            band = CoverageBand.partial_coverage
        else:
            band = CoverageBand.low_coverage

        return CoverageInfo(
            score=round(score, 1),
            band=band,
            events_received_24h=events_received_24h,
            expected_daily_events=expected_daily_events,
        )

    def _record_daily_count(self, client_id: str, agent_id: str, count: int) -> None:
        if not self._redis:
            return
        try:
            key = f"daily_event_history:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            history = json.loads(raw) if raw else []
            history.append(count)
            history = history[-7:]  # Keep last 7 days
            self._redis.set(key, json.dumps(history), ex=86400 * 10)
        except Exception:
            logger.warning("Failed to record daily event count")

    def _get_expected_daily(self, client_id: str, agent_id: str) -> int:
        if not self._redis:
            return 0
        try:
            key = f"daily_event_history:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            if raw:
                history = json.loads(raw)
                if len(history) >= 2:
                    avg = sum(history) / len(history)
                    return int(avg * settings.coverage_variance_tolerance)
        except Exception:
            logger.warning("Failed to get expected daily events")
        return 0
