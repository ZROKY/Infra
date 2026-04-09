"""Regression analyzer — promptfoo-style regression test scoring.

Tracks response consistency against baseline behavior patterns using
word overlap and structural similarity as proxy for regression test pass rate.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from ..models import AnalysisResult, AnalysisType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class RegressionAnalyzer:
    """Simulates promptfoo regression testing: compare response patterns against baseline."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self,
        prompt: str,
        response: str,
        client_id: str,
        agent_id: str,
    ) -> AnalysisResult:
        """Compare response against stored baseline for similar prompts."""
        prompt_key = self._normalize_prompt(prompt)
        baseline_response = self._get_baseline(client_id, agent_id, prompt_key)
        self._store_baseline(client_id, agent_id, prompt_key, response)

        if baseline_response is None:
            return AnalysisResult(
                analysis_type=AnalysisType.regression,
                score=85.0,
                confidence=0.3,
                details={"reason": "no_baseline_response"},
            )

        # Compare current response to baseline
        similarity = self._compute_similarity(baseline_response, response)
        structural_sim = self._structural_similarity(baseline_response, response)

        combined = similarity * 0.6 + structural_sim * 0.4
        score = min(100.0, combined * 100)

        return AnalysisResult(
            analysis_type=AnalysisType.regression,
            score=round(score, 1),
            confidence=0.7,
            threshold_exceeded=score < 60,
            details={
                "word_similarity": round(similarity, 3),
                "structural_similarity": round(structural_sim, 3),
                "combined": round(combined, 3),
            },
        )

    @staticmethod
    def _normalize_prompt(prompt: str) -> str:
        """Create a stable key for prompt deduplication."""
        words = sorted(set(re.findall(r"\b\w+\b", prompt.lower())))
        return ":".join(words[:20])

    @staticmethod
    def _compute_similarity(baseline: str, current: str) -> float:
        """Word-level Jaccard similarity."""
        b_words = set(re.findall(r"\b\w+\b", baseline.lower()))
        c_words = set(re.findall(r"\b\w+\b", current.lower()))
        if not b_words or not c_words:
            return 0.5
        intersection = len(b_words & c_words)
        union = len(b_words | c_words)
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def _structural_similarity(baseline: str, current: str) -> float:
        """Compare structural features: sentence count, avg length, format."""
        b_sents = [s.strip() for s in re.split(r"[.!?]+", baseline) if s.strip()]
        c_sents = [s.strip() for s in re.split(r"[.!?]+", current) if s.strip()]

        if not b_sents or not c_sents:
            return 0.5

        # Sentence count ratio
        count_ratio = min(len(b_sents), len(c_sents)) / max(len(b_sents), len(c_sents))

        # Length ratio
        b_len = len(baseline)
        c_len = len(current)
        len_ratio = min(b_len, c_len) / max(b_len, c_len) if max(b_len, c_len) > 0 else 1.0

        # Has similar formatting (lists, code blocks, headers)
        b_has_list = bool(re.search(r"^\s*[-*\d]\.", baseline, re.MULTILINE))
        c_has_list = bool(re.search(r"^\s*[-*\d]\.", current, re.MULTILINE))
        format_sim = 1.0 if b_has_list == c_has_list else 0.7

        return (count_ratio + len_ratio + format_sim) / 3

    def _get_baseline(self, client_id: str, agent_id: str, prompt_key: str) -> str | None:
        if not self._redis:
            return None
        try:
            key = f"regression_baseline:{client_id}:{agent_id}:{prompt_key}"
            raw = self._redis.get(key)
            return raw.decode("utf-8") if raw else None
        except Exception:
            logger.warning("Failed to read regression baseline")
        return None

    def _store_baseline(self, client_id: str, agent_id: str, prompt_key: str, response: str) -> None:
        if not self._redis:
            return
        try:
            key = f"regression_baseline:{client_id}:{agent_id}:{prompt_key}"
            # Only store if no baseline exists (preserve first-seen behavior)
            if not self._redis.exists(key):
                self._redis.set(key, response.encode("utf-8"), ex=86400 * 30)  # 30-day TTL
        except Exception:
            logger.warning("Failed to store regression baseline")
