"""System Engine orchestrator — runs all 7 monitors and computes the 0-100 system score.

Score formula (5 primary dimensions):
  system_score = (
      0.25 × latency
    + 0.20 × error_rate
    + 0.20 × cost
    + 0.20 × uptime
    + 0.15 × throughput
  )

Secondary monitors (cost_per_outcome, perf_quality_correlation) apply modifiers.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from .config import settings
from .models import (
    MonitorResult,
    SystemDetails,
    SystemEngineResult,
    SystemEventInput,
    SystemHealthLevel,
)
from .monitors import (
    CostMonitor,
    CostPerOutcomeMonitor,
    ErrorRateMonitor,
    LatencyMonitor,
    PerfQualityMonitor,
    ThroughputMonitor,
    UptimeMonitor,
)

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class SystemEngine:
    """Full System Engine pipeline — operational health monitoring."""

    def __init__(self, redis_client: Redis | None = None):
        self.latency = LatencyMonitor(redis_client=redis_client)
        self.error_rate = ErrorRateMonitor(redis_client=redis_client)
        self.cost = CostMonitor(redis_client=redis_client)
        self.uptime = UptimeMonitor(redis_client=redis_client)
        self.throughput = ThroughputMonitor(redis_client=redis_client)
        self.cost_per_outcome = CostPerOutcomeMonitor(redis_client=redis_client)
        self.perf_quality = PerfQualityMonitor(redis_client=redis_client)

    async def analyze(self, event: SystemEventInput) -> SystemEngineResult:
        """Run all 7 monitors and compute weighted system score."""
        start = time.monotonic()
        monitors: list[MonitorResult] = []

        # ── Primary monitors ───────────────────────────────────────────
        lat_result, lat_metrics = await self.latency.analyze(
            event.latency_ms, event.client_id, event.agent_id
        )
        monitors.append(lat_result)

        err_result = await self.error_rate.analyze(
            event.status_code, event.is_error, event.client_id, event.agent_id
        )
        monitors.append(err_result)

        cost_result, cost_metrics = await self.cost.analyze(
            event.cost_usd, event.prompt_tokens, event.completion_tokens,
            event.client_id, event.agent_id,
        )
        monitors.append(cost_result)

        uptime_result = await self.uptime.analyze(
            event.is_error, event.client_id, event.agent_id
        )
        monitors.append(uptime_result)

        tp_result, tp_metrics = await self.throughput.analyze(
            event.client_id, event.agent_id
        )
        monitors.append(tp_result)

        # ── Secondary monitors (modifiers) ─────────────────────────────
        cpo_result = await self.cost_per_outcome.analyze(
            event.cost_usd, event.quality_score, event.is_error,
            event.client_id, event.agent_id,
        )
        monitors.append(cpo_result)

        pq_result = await self.perf_quality.analyze(
            event.latency_ms, event.quality_score,
            event.client_id, event.agent_id,
        )
        monitors.append(pq_result)

        # ── Compute weighted score ─────────────────────────────────────
        system_score = (
            settings.weight_latency * lat_result.score
            + settings.weight_error_rate * err_result.score
            + settings.weight_cost * cost_result.score
            + settings.weight_uptime * uptime_result.score
            + settings.weight_throughput * tp_result.score
        )

        # Apply secondary modifiers
        # High waste ratio → penalize
        waste_ratio = cpo_result.details.get("waste_ratio_pct", 0)
        if waste_ratio > settings.waste_ratio_alert_pct:
            system_score *= 0.9

        # Strong negative perf-quality correlation → penalize
        pearson_r = pq_result.details.get("pearson_r", 0)
        if isinstance(pearson_r, (int, float)) and pearson_r < settings.correlation_alert_threshold:
            system_score *= 0.9

        system_score = round(max(0.0, min(100.0, system_score)), 1)
        level = self._score_to_level(system_score)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        error_rate_pct = err_result.details.get("error_rate_pct", 0.0)
        uptime_pct = uptime_result.details.get("uptime_pct", 100.0)

        details = SystemDetails(
            latency_score=round(lat_result.score, 1),
            error_score=round(err_result.score, 1),
            cost_score=round(cost_result.score, 1),
            uptime_score=round(uptime_result.score, 1),
            throughput_score=round(tp_result.score, 1),
            latency_metrics=lat_metrics,
            cost_metrics=cost_metrics,
            throughput_metrics=tp_metrics,
            uptime_pct=uptime_pct,
            error_rate_pct=error_rate_pct,
            waste_ratio=waste_ratio,
            perf_quality_correlation=pearson_r if isinstance(pearson_r, (int, float)) else 0.0,
            evaluation_latency_ms=elapsed_ms,
        )

        return SystemEngineResult(
            event_id=event.event_id,
            client_id=event.client_id,
            agent_id=event.agent_id,
            system_score=system_score,
            system_level=level,
            monitors=monitors,
            details=details,
        )

    @staticmethod
    def _score_to_level(score: float) -> SystemHealthLevel:
        if score >= 90:
            return SystemHealthLevel.optimal
        if score >= 70:
            return SystemHealthLevel.healthy
        if score >= 50:
            return SystemHealthLevel.degraded
        if score >= 30:
            return SystemHealthLevel.unhealthy
        return SystemHealthLevel.critical
