"""Behavioral fingerprint analyzer — weekly signature vector comparison.

Generates a behavioral fingerprint from response characteristics and
compares against previous fingerprints to detect "vibe shift".
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from ..config import settings
from ..models import AnalysisResult, AnalysisType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class FingerprintAnalyzer:
    """Detect behavioral shifts via response feature fingerprinting."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, response: str, client_id: str, agent_id: str
    ) -> AnalysisResult:
        """Generate fingerprint from response features and compare to historical."""
        fingerprint = self._generate_fingerprint(response)
        previous = self._get_previous_fingerprint(client_id, agent_id)
        self._store_fingerprint(client_id, agent_id, fingerprint)

        if previous is None:
            return AnalysisResult(
                analysis_type=AnalysisType.fingerprint,
                score=90.0,
                confidence=0.3,
                details={"reason": "no_previous_fingerprint"},
            )

        delta = self._compute_delta(previous, fingerprint)
        threshold_exceeded = delta > settings.fingerprint_delta_threshold

        # Convert delta to score (lower delta = higher score)
        score = max(0.0, 100.0 - delta * 500)

        return AnalysisResult(
            analysis_type=AnalysisType.fingerprint,
            score=round(score, 1),
            confidence=0.7,
            threshold_exceeded=threshold_exceeded,
            details={
                "delta": round(delta, 4),
                "threshold": settings.fingerprint_delta_threshold,
            },
        )

    @staticmethod
    def _generate_fingerprint(response: str) -> list[float]:
        """Create a feature vector from response characteristics."""
        words = response.split()
        sentences = [s.strip() for s in response.split(".") if s.strip()]

        word_count = len(words)
        char_count = len(response)
        sentence_count = len(sentences)
        avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
        avg_sentence_len = word_count / max(sentence_count, 1)

        # Vocabulary diversity
        unique_ratio = len(set(w.lower() for w in words)) / max(word_count, 1)

        # Structural features
        has_lists = 1.0 if any(line.strip().startswith(("-", "*", "1.")) for line in response.split("\n")) else 0.0
        has_code = 1.0 if "```" in response or "    " in response else 0.0
        question_marks = response.count("?") / max(sentence_count, 1)
        exclamation_marks = response.count("!") / max(sentence_count, 1)

        # Tone indicators
        uppercase_ratio = sum(1 for c in response if c.isupper()) / max(char_count, 1)
        digit_ratio = sum(1 for c in response if c.isdigit()) / max(char_count, 1)

        # Normalize all to 0-1 range
        return [
            min(1.0, word_count / 500),
            min(1.0, char_count / 2000),
            min(1.0, sentence_count / 20),
            min(1.0, avg_word_len / 10),
            min(1.0, avg_sentence_len / 30),
            unique_ratio,
            has_lists,
            has_code,
            min(1.0, question_marks),
            min(1.0, exclamation_marks),
            uppercase_ratio,
            digit_ratio,
        ]

    @staticmethod
    def _compute_delta(previous: list[float], current: list[float]) -> float:
        """Cosine distance between fingerprints."""
        a = np.array(previous)
        b = np.array(current)
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 1.0
        cosine_sim = float(dot / norm)
        return max(0.0, 1.0 - cosine_sim)

    def _get_previous_fingerprint(self, client_id: str, agent_id: str) -> list[float] | None:
        if not self._redis:
            return None
        try:
            import json
            key = f"fingerprint:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            logger.warning("Failed to read previous fingerprint")
        return None

    def _store_fingerprint(self, client_id: str, agent_id: str, fingerprint: list[float]) -> None:
        if not self._redis:
            return
        try:
            import json
            key = f"fingerprint:{client_id}:{agent_id}"
            self._redis.set(key, json.dumps(fingerprint), ex=86400 * 7)
        except Exception:
            logger.warning("Failed to store fingerprint")
