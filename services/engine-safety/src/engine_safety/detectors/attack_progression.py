"""Attack progression tracking — per-user sophistication over time."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import ActionTaken, AttackProgression, AttackStage, Detection, DetectionType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)

# Stage thresholds: cumulative flagged events raise stage
STAGE_THRESHOLDS = [
    (3, AttackStage.probing, ActionTaken.log),       # 3+ events → Probing
    (8, AttackStage.testing, ActionTaken.flag),       # 8+ events → Testing
    (15, AttackStage.exploiting, ActionTaken.block),  # 15+ events → Exploiting
    (25, AttackStage.exfiltrating, ActionTaken.block),# 25+ events → Exfiltrating
]


class AttackProgressionDetector:
    """
    Track per-user (session) attack sophistication over time.

    Uses Redis counters to accumulate flagged events per session and
    determines the current attack stage.
    """

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def detect(
        self,
        session_id: str,
        has_detections: bool,
    ) -> tuple[list[Detection], AttackProgression]:
        """Update attack progression for a session and return current stage."""
        if not session_id or self._redis is None:
            return [], AttackProgression()

        key = f"attack_prog:{session_id}"

        try:
            if has_detections:
                count = self._redis.incr(key)
                if count == 1:
                    # Track for 24 hours
                    self._redis.expire(key, 86400)
            else:
                raw = self._redis.get(key)
                count = int(raw) if raw else 0

            # Determine stage
            stage_idx = 0
            stage_name = AttackStage.probing
            action = ActionTaken.log

            for threshold, name, act in STAGE_THRESHOLDS:
                if count >= threshold:
                    stage_idx = STAGE_THRESHOLDS.index((threshold, name, act))
                    stage_name = name
                    action = act

            progression = AttackProgression(
                user_id=session_id,
                stage=stage_idx,
                stage_name=stage_name,
                auto_throttle=stage_idx >= 2,  # Throttle at Exploiting+
            )

            detections: list[Detection] = []
            if stage_idx >= 2:  # Only produce detection for Exploiting+
                detections.append(
                    Detection(
                        type=DetectionType.prompt_injection,
                        confidence=min(0.95, 0.70 + 0.05 * stage_idx),
                        action_taken=action,
                        details=f"Attack progression stage {stage_idx}: {stage_name.value} ({count} flagged events)",
                    )
                )

            return detections, progression

        except Exception:
            logger.warning("Attack progression Redis error", exc_info=True)
            return [], AttackProgression()
