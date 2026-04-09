"""Behavioral drift analyzer — statistical distribution shift detection (Evidently-style).

Computes PSI, KL Divergence, Wasserstein Distance, and JS Divergence
on response feature distributions using Redis-stored historical baselines.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from ..config import settings
from ..models import AnalysisResult, AnalysisType, DriftMetrics

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)

# Feature extraction bins for histograms
RESPONSE_LENGTH_BINS = [0, 50, 100, 200, 500, 1000, 2000, 5000, 10000, float("inf")]
WORD_COUNT_BINS = [0, 10, 25, 50, 100, 200, 500, 1000, float("inf")]


class DriftAnalyzer:
    """Statistical drift detection across response feature distributions."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(self, response: str, client_id: str, agent_id: str) -> tuple[list[AnalysisResult], DriftMetrics]:
        """Analyze response features against baseline distribution. Returns (results, metrics)."""
        features = self._extract_features(response)

        # Get/update running distribution from Redis
        baseline = self._get_baseline(client_id, agent_id)
        self._update_baseline(client_id, agent_id, features)

        if not baseline or len(baseline.get("response_lengths", [])) < 10:
            # Not enough data for drift detection
            return (
                [AnalysisResult(
                    analysis_type=AnalysisType.drift_psi,
                    score=90.0,
                    confidence=0.2,
                    details={"reason": "insufficient_baseline_data"},
                )],
                DriftMetrics(),
            )

        # Compute drift metrics
        current_lengths = baseline.get("response_lengths", [])[-50:] + [features["response_length"]]
        historical_lengths = baseline.get("response_lengths", [])[:-50] or baseline.get("response_lengths", [])

        if len(historical_lengths) < 5 or len(current_lengths) < 5:
            return (
                [AnalysisResult(
                    analysis_type=AnalysisType.drift_psi,
                    score=85.0,
                    confidence=0.3,
                    details={"reason": "insufficient_window_data"},
                )],
                DriftMetrics(),
            )

        psi = self._compute_psi(historical_lengths, current_lengths, RESPONSE_LENGTH_BINS)
        kl = self._compute_kl_divergence(historical_lengths, current_lengths, RESPONSE_LENGTH_BINS)
        wasserstein = self._compute_wasserstein(historical_lengths, current_lengths)
        js = self._compute_js_divergence(historical_lengths, current_lengths, RESPONSE_LENGTH_BINS)

        drift_detected = (
            psi > settings.drift_psi_threshold
            or kl > settings.drift_kl_threshold
            or wasserstein > settings.drift_wasserstein_threshold
            or js > settings.drift_js_threshold
        )

        metrics = DriftMetrics(
            psi=round(psi, 4),
            kl_divergence=round(kl, 4),
            wasserstein=round(wasserstein, 4),
            js_divergence=round(js, 4),
            drift_detected=drift_detected,
        )

        results = [
            AnalysisResult(
                analysis_type=AnalysisType.drift_psi,
                score=max(0, 100 - psi * 300),
                confidence=0.8,
                threshold_exceeded=psi > settings.drift_psi_threshold,
                details={"value": round(psi, 4), "threshold": settings.drift_psi_threshold},
            ),
            AnalysisResult(
                analysis_type=AnalysisType.drift_kl,
                score=max(0, 100 - kl * 400),
                confidence=0.8,
                threshold_exceeded=kl > settings.drift_kl_threshold,
                details={"value": round(kl, 4), "threshold": settings.drift_kl_threshold},
            ),
            AnalysisResult(
                analysis_type=AnalysisType.drift_wasserstein,
                score=max(0, 100 - wasserstein * 400),
                confidence=0.8,
                threshold_exceeded=wasserstein > settings.drift_wasserstein_threshold,
                details={"value": round(wasserstein, 4), "threshold": settings.drift_wasserstein_threshold},
            ),
            AnalysisResult(
                analysis_type=AnalysisType.drift_js,
                score=max(0, 100 - js * 400),
                confidence=0.8,
                threshold_exceeded=js > settings.drift_js_threshold,
                details={"value": round(js, 4), "threshold": settings.drift_js_threshold},
            ),
        ]

        return results, metrics

    @staticmethod
    def _extract_features(response: str) -> dict:
        words = response.split()
        return {
            "response_length": len(response),
            "word_count": len(words),
            "avg_word_length": sum(len(w) for w in words) / max(len(words), 1),
        }

    def _get_baseline(self, client_id: str, agent_id: str) -> dict | None:
        if not self._redis:
            return None
        try:
            import json
            key = f"drift_baseline:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            logger.warning("Failed to read drift baseline from Redis")
        return None

    def _update_baseline(self, client_id: str, agent_id: str, features: dict) -> None:
        if not self._redis:
            return
        try:
            import json
            key = f"drift_baseline:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            baseline = json.loads(raw) if raw else {"response_lengths": [], "word_counts": []}

            baseline["response_lengths"].append(features["response_length"])
            baseline["word_counts"].append(features["word_count"])

            # Keep last 1000 entries
            baseline["response_lengths"] = baseline["response_lengths"][-1000:]
            baseline["word_counts"] = baseline["word_counts"][-1000:]

            self._redis.set(key, json.dumps(baseline), ex=86400 * 7)  # 7-day TTL
        except Exception:
            logger.warning("Failed to update drift baseline in Redis")

    @staticmethod
    def _histogram(data: list, bins: list) -> np.ndarray:
        counts, _ = np.histogram(data, bins=bins)
        # Add small epsilon to avoid division by zero
        return (counts + 1e-10) / (sum(counts) + len(counts) * 1e-10)

    @classmethod
    def _compute_psi(cls, baseline: list, current: list, bins: list) -> float:
        """Population Stability Index."""
        p = cls._histogram(baseline, bins)
        q = cls._histogram(current, bins)
        return float(np.sum((p - q) * np.log(p / q)))

    @classmethod
    def _compute_kl_divergence(cls, baseline: list, current: list, bins: list) -> float:
        """Kullback-Leibler divergence."""
        p = cls._histogram(baseline, bins)
        q = cls._histogram(current, bins)
        return float(np.sum(p * np.log(p / q)))

    @staticmethod
    def _compute_wasserstein(baseline: list, current: list) -> float:
        """Wasserstein (earth mover's) distance, normalized to 0-1 range."""
        a = np.sort(baseline)
        b = np.sort(current)
        # Interpolate to same length
        n = max(len(a), len(b))
        a_interp = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(a)), a)
        b_interp = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(b)), b)
        distance = float(np.mean(np.abs(a_interp - b_interp)))
        # Normalize by max range
        max_range = max(max(baseline + current) - min(baseline + current), 1)
        return distance / max_range

    @classmethod
    def _compute_js_divergence(cls, baseline: list, current: list, bins: list) -> float:
        """Jensen-Shannon divergence (symmetric KL)."""
        p = cls._histogram(baseline, bins)
        q = cls._histogram(current, bins)
        m = 0.5 * (p + q)
        kl_pm = float(np.sum(p * np.log(p / m)))
        kl_qm = float(np.sum(q * np.log(q / m)))
        return 0.5 * (kl_pm + kl_qm)
