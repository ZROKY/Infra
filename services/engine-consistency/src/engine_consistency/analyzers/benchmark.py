"""Benchmark analyzer — daily benchmark testing via response quality scoring.

Simulates lm-evaluation-harness style benchmark evaluation by scoring
response quality against known patterns and historical baselines.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..config import settings
from ..models import AnalysisResult, AnalysisType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class BenchmarkAnalyzer:
    """Track daily benchmark scores and detect degradation."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, response: str, client_id: str, agent_id: str
    ) -> AnalysisResult:
        """Score response quality and compare against rolling baseline."""
        # Compute quality signals
        quality_score = self._compute_quality_score(response)

        # Get historical baseline
        baseline_avg = self._get_rolling_avg(client_id, agent_id)
        self._update_rolling_avg(client_id, agent_id, quality_score)

        if baseline_avg is None:
            return AnalysisResult(
                analysis_type=AnalysisType.benchmark,
                score=quality_score,
                confidence=0.4,
                details={"reason": "no_baseline", "quality_score": quality_score},
            )

        drop_pct = ((baseline_avg - quality_score) / max(baseline_avg, 1)) * 100
        threshold_exceeded = drop_pct > settings.benchmark_drop_alert_pct

        # Score = how well current compares to baseline
        if quality_score >= baseline_avg:
            final_score = min(100.0, quality_score)
        else:
            final_score = max(0.0, quality_score - (drop_pct * 0.5))

        return AnalysisResult(
            analysis_type=AnalysisType.benchmark,
            score=round(final_score, 1),
            confidence=0.7,
            threshold_exceeded=threshold_exceeded,
            details={
                "quality_score": round(quality_score, 1),
                "baseline_avg": round(baseline_avg, 1),
                "drop_pct": round(drop_pct, 1),
            },
        )

    @staticmethod
    def _compute_quality_score(response: str) -> float:
        """Heuristic quality scoring based on response characteristics."""
        if not response.strip():
            return 0.0

        score = 70.0  # Base score

        words = response.split()
        word_count = len(words)

        # Length bonus (10-500 words is optimal)
        if 10 <= word_count <= 500:
            score += 10.0
        elif word_count < 10:
            score -= 15.0
        elif word_count > 1000:
            score -= 5.0

        # Sentence structure (has punctuation)
        if any(c in response for c in ".!?"):
            score += 5.0

        # Vocabulary diversity
        unique_words = len(set(w.lower() for w in words))
        if word_count > 0:
            diversity = unique_words / word_count
            if diversity > 0.5:
                score += 5.0
            elif diversity < 0.2:
                score -= 5.0

        # Capitalization (proper sentences)
        sentences = response.split(".")
        properly_capitalized = sum(1 for s in sentences if s.strip() and s.strip()[0].isupper())
        if sentences and properly_capitalized / max(len(sentences), 1) > 0.5:
            score += 5.0

        return max(0.0, min(100.0, score))

    def _get_rolling_avg(self, client_id: str, agent_id: str) -> float | None:
        if not self._redis:
            return None
        try:
            import json
            key = f"benchmark_history:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            if raw:
                history = json.loads(raw)
                if history:
                    return sum(history) / len(history)
        except Exception:
            logger.warning("Failed to read benchmark history")
        return None

    def _update_rolling_avg(self, client_id: str, agent_id: str, score: float) -> None:
        if not self._redis:
            return
        try:
            import json
            key = f"benchmark_history:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            history = json.loads(raw) if raw else []
            history.append(score)
            history = history[-100:]  # Keep last 100
            self._redis.set(key, json.dumps(history), ex=86400 * 7)
        except Exception:
            logger.warning("Failed to update benchmark history")
