"""Cost-per-outcome monitor — waste ratio analysis."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..config import settings
from ..models import MonitorResult, MonitorType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class CostPerOutcomeMonitor:
    """Track cost/success vs cost/failure and compute waste ratio."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, cost_usd: float, quality_score: float, is_error: bool,
        client_id: str, agent_id: str,
    ) -> MonitorResult:
        """Compute waste ratio: cost spent on failed/low-quality outcomes."""
        is_wasted = is_error or quality_score < 50.0
        self._record(client_id, agent_id, cost_usd, is_wasted)
        total_cost, wasted_cost = self._get_totals(client_id, agent_id)

        total_cost += cost_usd
        if is_wasted:
            wasted_cost += cost_usd

        waste_ratio = (wasted_cost / max(total_cost, 0.001)) * 100

        # Score: 0% waste → 100, ≥20% waste → starts degrading
        if waste_ratio <= 5:
            score = 100.0
        elif waste_ratio <= settings.waste_ratio_alert_pct:
            ratio = (waste_ratio - 5) / max(settings.waste_ratio_alert_pct - 5, 1)
            score = 100.0 - ratio * 40.0  # 60-100
        elif waste_ratio <= 50:
            score = 60.0 - (waste_ratio - settings.waste_ratio_alert_pct) * 1.5
        else:
            score = max(0.0, 15.0 - (waste_ratio - 50) * 0.3)

        return MonitorResult(
            monitor_type=MonitorType.cost_per_outcome,
            score=round(score, 1),
            confidence=0.7,
            threshold_exceeded=waste_ratio > settings.waste_ratio_alert_pct,
            details={
                "waste_ratio_pct": round(waste_ratio, 2),
                "total_cost": round(total_cost, 4),
                "wasted_cost": round(wasted_cost, 4),
                "alert_threshold_pct": settings.waste_ratio_alert_pct,
            },
        )

    def _record(self, client_id: str, agent_id: str, cost: float, wasted: bool) -> None:
        if not self._redis:
            return
        try:
            total_key = f"outcome_cost_total:{client_id}:{agent_id}"
            waste_key = f"outcome_cost_waste:{client_id}:{agent_id}"
            pipe = self._redis.pipeline()
            pipe.incrbyfloat(total_key, cost)
            if wasted:
                pipe.incrbyfloat(waste_key, cost)
            pipe.expire(total_key, 86400)
            pipe.expire(waste_key, 86400)
            pipe.execute()
        except Exception:
            logger.warning("Failed to record cost-per-outcome")

    def _get_totals(self, client_id: str, agent_id: str) -> tuple[float, float]:
        if not self._redis:
            return 0.0, 0.0
        try:
            total_key = f"outcome_cost_total:{client_id}:{agent_id}"
            waste_key = f"outcome_cost_waste:{client_id}:{agent_id}"
            total = self._redis.get(total_key)
            waste = self._redis.get(waste_key)
            return float(total or 0), float(waste or 0)
        except Exception:
            logger.warning("Failed to get cost-per-outcome totals")
        return 0.0, 0.0
