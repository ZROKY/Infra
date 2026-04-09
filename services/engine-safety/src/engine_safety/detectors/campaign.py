"""Campaign detection — 50+ similar attacks in 1h triggers CRITICAL alert."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import ActionTaken, Detection, DetectionType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class CampaignDetector:
    """
    Detect coordinated attack campaigns using Redis counters.

    A campaign is triggered when 50+ events with detections (block/flag actions)
    are seen for the same client within a 1-hour window.
    """

    def __init__(self, redis_client: Redis | None = None, threshold: int = 50, window: int = 3600):
        self._redis = redis_client
        self._threshold = threshold
        self._window = window

    async def detect(
        self,
        client_id: str,
        agent_id: str,
        has_detections: bool,
    ) -> list[Detection]:
        """Check if attack volume constitutes a campaign."""
        if not has_detections or self._redis is None:
            return []

        key = f"campaign:{client_id}:{agent_id}"
        try:
            count = self._redis.incr(key)
            if count == 1:
                self._redis.expire(key, self._window)

            if count >= self._threshold:
                return [
                    Detection(
                        type=DetectionType.campaign,
                        confidence=min(0.99, 0.80 + 0.01 * (count - self._threshold)),
                        action_taken=ActionTaken.escalate,
                        details=f"Coordinated campaign: {count} flagged events in window",
                    )
                ]
        except Exception:
            logger.warning("Campaign detection Redis error", exc_info=True)

        return []
