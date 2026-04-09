"""Cost monitor — token-level cost tracking with budget alerts."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from ..config import settings
from ..models import CostMetrics, MonitorResult, MonitorType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class CostMonitor:
    """Track per-event and cumulative costs against daily/monthly budgets."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, cost_usd: float, prompt_tokens: int, completion_tokens: int,
        client_id: str, agent_id: str,
    ) -> tuple[MonitorResult, CostMetrics]:
        """Score cost efficiency and budget consumption. Returns (result, metrics)."""
        self._record_cost(client_id, agent_id, cost_usd)
        daily_total, monthly_total = self._get_totals(client_id, agent_id)

        daily_total += cost_usd
        monthly_total += cost_usd

        total_tokens = prompt_tokens + completion_tokens
        cost_per_1k = (cost_usd / max(total_tokens, 1)) * 1000

        daily_pct = (daily_total / max(settings.daily_cost_budget, 0.01)) * 100
        monthly_pct = (monthly_total / max(settings.monthly_cost_budget, 0.01)) * 100

        metrics = CostMetrics(
            event_cost_usd=round(cost_usd, 6),
            daily_total_usd=round(daily_total, 4),
            monthly_total_usd=round(monthly_total, 4),
            daily_budget_pct=round(daily_pct, 1),
            monthly_budget_pct=round(monthly_pct, 1),
            cost_per_1k_tokens=round(cost_per_1k, 6),
        )

        # Score: under 50% budget → 100, over 100% → 0
        max_pct = max(daily_pct, monthly_pct)
        if max_pct <= 50:
            score = 100.0
        elif max_pct <= 75:
            score = 100.0 - (max_pct - 50) * 1.2  # 70-100
        elif max_pct <= 100:
            score = 70.0 - (max_pct - 75) * 2.0  # 20-70
        else:
            score = max(0.0, 20.0 - (max_pct - 100) * 0.5)

        # Check which alert thresholds are exceeded
        exceeded_thresholds = [t for t in settings.cost_alert_thresholds if max_pct >= t]

        return MonitorResult(
            monitor_type=MonitorType.cost,
            score=round(score, 1),
            confidence=0.9,
            threshold_exceeded=bool(exceeded_thresholds),
            details={
                "daily_budget_pct": round(daily_pct, 1),
                "monthly_budget_pct": round(monthly_pct, 1),
                "exceeded_thresholds": exceeded_thresholds,
            },
        ), metrics

    def _record_cost(self, client_id: str, agent_id: str, cost_usd: float) -> None:
        if not self._redis:
            return
        try:
            today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
            month = datetime.now(tz=UTC).strftime("%Y-%m")
            daily_key = f"cost_daily:{client_id}:{agent_id}:{today}"
            monthly_key = f"cost_monthly:{client_id}:{agent_id}:{month}"
            pipe = self._redis.pipeline()
            pipe.incrbyfloat(daily_key, cost_usd)
            pipe.incrbyfloat(monthly_key, cost_usd)
            pipe.expire(daily_key, 86400)
            pipe.expire(monthly_key, 86400 * 31)
            pipe.execute()
        except Exception:
            logger.warning("Failed to record cost")

    def _get_totals(self, client_id: str, agent_id: str) -> tuple[float, float]:
        if not self._redis:
            return 0.0, 0.0
        try:
            today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
            month = datetime.now(tz=UTC).strftime("%Y-%m")
            daily_key = f"cost_daily:{client_id}:{agent_id}:{today}"
            monthly_key = f"cost_monthly:{client_id}:{agent_id}:{month}"
            daily = self._redis.get(daily_key)
            monthly = self._redis.get(monthly_key)
            return float(daily or 0), float(monthly or 0)
        except Exception:
            logger.warning("Failed to get cost totals")
        return 0.0, 0.0
