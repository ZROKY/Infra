"""Golden test evaluator — compare response against known-correct answers.

Clients provide golden datasets (question → expected answer pairs).
This evaluator measures semantic similarity between actual and expected answers.
"""

from __future__ import annotations

import logging
import re

import httpx
import numpy as np

from ..config import settings
from ..models import EvaluationResult, EvaluationType

logger = logging.getLogger(__name__)


class GoldenTestEvaluator:
    """Compare AI response against ground-truth expected answer via embedding similarity."""

    async def evaluate(
        self,
        response: str,
        ground_truth: str | None,
    ) -> EvaluationResult:
        if not ground_truth:
            return EvaluationResult(
                evaluation_type=EvaluationType.golden_test,
                score=0.0,
                confidence=0.0,
                details={"reason": "no_ground_truth_provided", "skipped": True},
            )

        try:
            embeddings = await self._get_embeddings([response, ground_truth])
            if len(embeddings) == 2:
                similarity = self._cosine_similarity(embeddings[0], embeddings[1])
                # Map cosine similarity (typically 0.5-1.0 for text) to 0-100
                score = max(0.0, min(100.0, (similarity - 0.5) * 200))

                return EvaluationResult(
                    evaluation_type=EvaluationType.golden_test,
                    score=round(score, 1),
                    confidence=0.9,
                    details={
                        "cosine_similarity": round(similarity, 4),
                        "method": "embedding_similarity",
                    },
                )
        except (httpx.HTTPError, TimeoutError):
            logger.warning("Embedding service unavailable — using word overlap")

        return self._heuristic_similarity(response, ground_truth)

    @staticmethod
    async def _get_embeddings(texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=settings.embedding_timeout) as client:
            resp = await client.post(
                settings.embedding_url,
                json={"model": settings.embedding_model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        a_arr, b_arr = np.array(a), np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
        if norm == 0:
            return 0.0
        return float(dot / norm)

    @staticmethod
    def _heuristic_similarity(response: str, ground_truth: str) -> EvaluationResult:
        """Fallback: word-level Jaccard similarity."""
        # Clean and normalize
        r_words = set(re.findall(r"\b\w+\b", response.lower()))
        g_words = set(re.findall(r"\b\w+\b", ground_truth.lower()))

        # Remove very common stopwords
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "in", "on", "at", "to", "for", "of", "and", "or", "but", "it", "its", "this", "that"}
        r_words -= stopwords
        g_words -= stopwords

        if not r_words or not g_words:
            return EvaluationResult(
                evaluation_type=EvaluationType.golden_test,
                score=30.0,
                confidence=0.2,
                details={"method": "empty_comparison"},
            )

        intersection = len(r_words & g_words)
        union = len(r_words | g_words)
        jaccard = intersection / union if union > 0 else 0

        # Scale Jaccard (typically 0.1-0.6 for semantic matches) to 0-100
        score = min(100.0, jaccard * 180)

        return EvaluationResult(
            evaluation_type=EvaluationType.golden_test,
            score=round(score, 1),
            confidence=0.4,
            details={
                "method": "jaccard_similarity",
                "jaccard": round(jaccard, 4),
                "shared_terms": intersection,
            },
        )
