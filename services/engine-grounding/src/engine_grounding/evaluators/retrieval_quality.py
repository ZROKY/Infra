"""Retrieval quality evaluator — vector DB health and retrieval relevance monitoring.

Processes the rag_context field from events to assess retrieval performance.
"""

from __future__ import annotations

import logging

from ..config import settings
from ..models import EvaluationResult, EvaluationType, RAGContext

logger = logging.getLogger(__name__)


class RetrievalQualityEvaluator:
    """Assess retrieval quality from RAG context metadata."""

    async def evaluate(self, rag_context: RAGContext | None) -> EvaluationResult:
        if not rag_context or not rag_context.retrieved_chunks:
            return EvaluationResult(
                evaluation_type=EvaluationType.retrieval_quality,
                score=50.0,
                confidence=0.2,
                details={"reason": "no_rag_context", "skipped": True},
            )

        scores: list[float] = []
        chunk_details: list[dict] = []

        # 1. Retrieval score from vector DB (if provided)
        if rag_context.retrieval_score is not None:
            # Normalize to 0-100 (retrieval_score is typically 0-1 cosine similarity)
            retrieval_pct = rag_context.retrieval_score * 100
            scores.append(retrieval_pct)

        # 2. Per-chunk scores
        chunk_scores = []
        for chunk in rag_context.retrieved_chunks:
            if chunk.score is not None:
                chunk_scores.append(chunk.score * 100)
            elif chunk.content:
                # Chunk exists but no score — assume moderate quality
                chunk_scores.append(70.0)

        if chunk_scores:
            avg_chunk_score = sum(chunk_scores) / len(chunk_scores)
            scores.append(avg_chunk_score)
            chunk_details = [
                {"chunk_id": c.id, "score": round(c.score * 100, 1) if c.score else None}
                for c in rag_context.retrieved_chunks[:10]
            ]

        # 3. Chunk count quality signal (too few or too many chunks)
        num_chunks = len(rag_context.retrieved_chunks)
        if num_chunks == 0:
            count_penalty = 0.0
        elif 1 <= num_chunks <= 2:
            count_penalty = 0.9  # Few chunks — possibly insufficient
        elif 3 <= num_chunks <= 8:
            count_penalty = 1.0  # Optimal range
        else:
            count_penalty = 0.85  # Too many — noise risk

        # 4. Empty chunk detection
        non_empty_chunks = sum(1 for c in rag_context.retrieved_chunks if c.content.strip())
        content_ratio = non_empty_chunks / num_chunks if num_chunks > 0 else 0.0

        # Compute final score
        base_score = sum(scores) / len(scores) if scores else 70.0

        final_score = base_score * count_penalty * max(content_ratio, 0.5)
        final_score = max(0.0, min(100.0, final_score))

        # Determine health status
        if final_score >= settings.retrieval_relevance_alert:
            health = "healthy"
        elif final_score >= 60:
            health = "degraded"
        else:
            health = "critical"

        return EvaluationResult(
            evaluation_type=EvaluationType.retrieval_quality,
            score=round(final_score, 1),
            confidence=0.7 if scores else 0.4,
            details={
                "vector_db_type": rag_context.vector_store_type,
                "num_chunks": num_chunks,
                "non_empty_chunks": non_empty_chunks,
                "avg_distance": round(rag_context.retrieval_score, 4) if rag_context.retrieval_score else None,
                "chunk_details": chunk_details,
                "health": health,
            },
        )
