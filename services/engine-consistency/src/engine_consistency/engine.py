"""Consistency Engine orchestrator — runs all 5 analyzers and computes the 0-100 score.

Score formula:
  consistency_score = (
      0.20 × benchmark
    + 0.25 × regression
    + 0.25 × drift (avg of PSI/KL/Wasserstein/JS scores)
    + 0.15 × fingerprint
    + 0.15 × version_tracking
  )
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from .analyzers import (
    BenchmarkAnalyzer,
    DriftAnalyzer,
    FingerprintAnalyzer,
    RegressionAnalyzer,
    VersionTracker,
)
from .config import settings
from .models import (
    AnalysisResult,
    ConsistencyDetails,
    ConsistencyEngineResult,
    ConsistencyEventInput,
    ConsistencyLevel,
)

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class ConsistencyEngine:
    """Full Consistency Engine pipeline — behavioral drift, regression, and benchmarking."""

    def __init__(self, redis_client: Redis | None = None):
        self.benchmark = BenchmarkAnalyzer(redis_client=redis_client)
        self.regression = RegressionAnalyzer(redis_client=redis_client)
        self.drift = DriftAnalyzer(redis_client=redis_client)
        self.fingerprint = FingerprintAnalyzer(redis_client=redis_client)
        self.version_tracker = VersionTracker(redis_client=redis_client)

    async def analyze(self, event: ConsistencyEventInput) -> ConsistencyEngineResult:
        """Run the full consistency analysis pipeline."""
        start = time.monotonic()
        analyses: list[AnalysisResult] = []

        # 1. Benchmark
        bench_result = await self.benchmark.analyze(
            event.response, event.client_id, event.agent_id
        )
        analyses.append(bench_result)

        # 2. Regression
        reg_result = await self.regression.analyze(
            event.prompt, event.response, event.client_id, event.agent_id
        )
        analyses.append(reg_result)

        # 3. Drift (returns multiple results + metrics)
        drift_results, drift_metrics = await self.drift.analyze(
            event.response, event.client_id, event.agent_id
        )
        analyses.extend(drift_results)

        # 4. Fingerprint
        fp_result = await self.fingerprint.analyze(
            event.response, event.client_id, event.agent_id
        )
        analyses.append(fp_result)

        # 5. Version tracking
        ver_result = await self.version_tracker.analyze(
            event.model, event.model_version_str, event.client_id, event.agent_id
        )
        analyses.append(ver_result)

        # ── Compute weighted score ─────────────────────────────────────
        drift_avg_score = (
            sum(r.score for r in drift_results) / len(drift_results) if drift_results else 85.0
        )

        consistency_score = (
            settings.weight_benchmark * bench_result.score
            + settings.weight_regression * reg_result.score
            + settings.weight_drift * drift_avg_score
            + settings.weight_fingerprint * fp_result.score
            + settings.weight_version_tracking * ver_result.score
        )

        consistency_score = round(max(0.0, min(100.0, consistency_score)), 1)
        level = self._score_to_level(consistency_score)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        version_changed = ver_result.details.get("version_changed", False)

        details = ConsistencyDetails(
            benchmark_score=round(bench_result.score, 1),
            regression_test_score=round(reg_result.score, 1),
            drift_metrics=drift_metrics,
            fingerprint_delta=fp_result.details.get("delta", 0.0),
            model_version=event.model_version_str or event.model,
            model_version_changed=version_changed,
            drift_detected=drift_metrics.drift_detected,
            drift_magnitude=round(drift_metrics.psi * 100, 1) if drift_metrics.drift_detected else 0.0,
            evaluation_latency_ms=elapsed_ms,
        )

        return ConsistencyEngineResult(
            event_id=event.event_id,
            client_id=event.client_id,
            agent_id=event.agent_id,
            consistency_score=consistency_score,
            consistency_level=level,
            analyses=analyses,
            details=details,
        )

    @staticmethod
    def _score_to_level(score: float) -> ConsistencyLevel:
        if score >= 90:
            return ConsistencyLevel.stable
        if score >= 70:
            return ConsistencyLevel.nominal
        if score >= 50:
            return ConsistencyLevel.degraded
        if score >= 30:
            return ConsistencyLevel.unstable
        return ConsistencyLevel.critical
