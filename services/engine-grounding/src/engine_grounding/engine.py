"""Grounding Engine orchestrator — runs all evaluators and computes the 0-100 score.

Score formula (from V1 Scope):
  grounding_score = (
      0.25 × retrieval_quality
    + 0.25 × faithfulness (answer-source consistency)
    + 0.15 × consistency (factual consistency)
    + 0.20 × claim_attribution (Ragas: precision + recall + relevancy)
    + 0.15 × hallucination_metrics (DeepEval: inverted hallucination rate)
  )

Override rules:
  - If hallucination_rate > 10% in 1h window → grounding_score drops minimum 20 points
  - If contextual_relevancy < 70 → grounding_score *= 0.9
  - If answer_correctness < 60 → grounding_score *= 0.85
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from .config import settings
from .evaluators import (
    AnswerRelevancyEvaluator,
    ConsistencyEvaluator,
    ContextQualityEvaluator,
    FaithfulnessEvaluator,
    GoldenTestEvaluator,
    HallucinationEvaluator,
    RetrievalQualityEvaluator,
)
from .models import (
    DeepEvalMetrics,
    EvaluationResult,
    GroundingDetails,
    GroundingEngineResult,
    GroundingEventInput,
    GroundingLevel,
    RagasMetrics,
)

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class GroundingEngine:
    """Full Grounding Engine pipeline — evaluates RAG quality, hallucination, and factual accuracy."""

    def __init__(self, redis_client: Redis | None = None):
        self.redis_client = redis_client
        self.faithfulness = FaithfulnessEvaluator()
        self.answer_relevancy = AnswerRelevancyEvaluator()
        self.context_quality = ContextQualityEvaluator()
        self.hallucination = HallucinationEvaluator()
        self.consistency = ConsistencyEvaluator()
        self.golden_tests = GoldenTestEvaluator()
        self.retrieval_quality = RetrievalQualityEvaluator()

    async def analyze(self, event: GroundingEventInput) -> GroundingEngineResult:
        """Run the full grounding analysis pipeline for a single event."""
        start = time.monotonic()
        evaluations: list[EvaluationResult] = []
        has_rag = event.rag_context is not None and len(event.rag_context.retrieved_chunks) > 0
        source_chunks = [c.content for c in event.rag_context.retrieved_chunks] if has_rag else []

        # ── Step 1: Run all evaluators ─────────────────────────────────

        # 1a. Retrieval quality (from RAG metadata)
        retrieval_result = await self.retrieval_quality.evaluate(event.rag_context)
        evaluations.append(retrieval_result)

        # 1b. Faithfulness (claim-level attribution)
        faith_result = await self.faithfulness.evaluate(event.response, source_chunks)
        evaluations.append(faith_result)

        # 1c. Answer relevancy
        relevancy_result = await self.answer_relevancy.evaluate(event.prompt, event.response)
        evaluations.append(relevancy_result)

        # 1d. Context quality (precision + recall)
        precision_result, recall_result = await self.context_quality.evaluate(
            event.prompt, event.response, source_chunks
        )
        evaluations.extend([precision_result, recall_result])

        # 1e. Hallucination detection
        hallucination_result = await self.hallucination.evaluate(
            event.prompt, event.response, source_chunks
        )
        evaluations.append(hallucination_result)

        # 1f. Factual consistency
        consistency_result = await self.consistency.evaluate(
            event.prompt, event.response, source_chunks or None
        )
        evaluations.append(consistency_result)

        # 1g. Golden test (if ground truth provided)
        golden_result = await self.golden_tests.evaluate(event.response, event.ground_truth)
        evaluations.append(golden_result)

        # ── Step 2: Compute weighted score ─────────────────────────────

        # Extract raw scores
        retrieval_score = retrieval_result.score
        faithfulness_score = faith_result.score
        relevancy_score = relevancy_result.score
        precision_score = precision_result.score
        recall_score = recall_result.score
        hallucination_score = hallucination_result.score  # Already inverted (100 = no hallucination)
        consistency_score = consistency_result.score

        # Claim attribution = average of precision, recall, and relevancy (Ragas trio)
        claim_attribution = (precision_score + recall_score + relevancy_score) / 3

        # Weighted formula
        grounding_score = (
            settings.weight_retrieval_quality * retrieval_score
            + settings.weight_answer_source_consistency * faithfulness_score
            + settings.weight_factual_consistency * consistency_score
            + settings.weight_claim_attribution * claim_attribution
            + settings.weight_hallucination_metrics * hallucination_score
        )

        # ── Step 3: Apply DeepEval modifiers ───────────────────────────

        hallucination_details = hallucination_result.details
        contextual_relevancy = hallucination_details.get("contextual_relevancy", 100)
        answer_correctness = hallucination_details.get("answer_correctness", 100)

        if contextual_relevancy is not None and contextual_relevancy < 70:
            grounding_score *= 0.9
        if answer_correctness is not None and answer_correctness < 60:
            grounding_score *= 0.85

        # ── Step 4: Apply hallucination override ───────────────────────

        hallucination_override = False
        hallucination_rate = hallucination_details.get("hallucination_rate")
        if hallucination_rate is not None and hallucination_rate > settings.hallucination_critical_rate * 100:
            grounding_score = max(40, grounding_score - settings.hallucination_override_penalty)
            hallucination_override = True

        # ── Step 5: Clamp + classify ───────────────────────────────────

        grounding_score = round(max(0.0, min(100.0, grounding_score)), 1)
        grounding_level = self._score_to_level(grounding_score)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        # ── Build details ──────────────────────────────────────────────

        details = GroundingDetails(
            retrieval_relevance=round(retrieval_score, 1),
            faithfulness_score=round(faithfulness_score, 1),
            answer_relevancy=round(relevancy_score, 1),
            context_precision=round(precision_score, 1),
            context_recall=round(recall_score, 1),
            hallucination_rate=round(hallucination_rate, 1) if hallucination_rate is not None else 0.0,
            contextual_relevancy=round(contextual_relevancy, 1) if contextual_relevancy is not None else 0.0,
            answer_correctness=round(answer_correctness, 1) if answer_correctness is not None else 0.0,
            golden_test_score=round(golden_result.score, 1) if golden_result.confidence > 0 else None,
            vector_db_distance=event.rag_context.retrieval_score if has_rag and event.rag_context.retrieval_score else None,
            ragas_evaluation=RagasMetrics(
                faithfulness=round(faithfulness_score, 1),
                answer_relevancy=round(relevancy_score, 1),
                context_precision=round(precision_score, 1),
                context_recall=round(recall_score, 1),
            ),
            deepeval_evaluation=DeepEvalMetrics(
                hallucination_rate=round(hallucination_rate, 1) if hallucination_rate is not None else 0.0,
                contextual_relevancy=round(contextual_relevancy, 1) if contextual_relevancy is not None else 0.0,
                answer_correctness=round(answer_correctness, 1) if answer_correctness is not None else 0.0,
            ),
            evaluation_latency_ms=elapsed_ms,
            vector_db_type=event.rag_context.vector_store_type if has_rag else "",
        )

        return GroundingEngineResult(
            event_id=event.event_id,
            client_id=event.client_id,
            agent_id=event.agent_id,
            grounding_score=grounding_score,
            grounding_level=grounding_level,
            evaluations=evaluations,
            details=details,
            has_rag_context=has_rag,
            hallucination_override_applied=hallucination_override,
        )

    @staticmethod
    def _score_to_level(score: float) -> GroundingLevel:
        if score >= 90:
            return GroundingLevel.excellent
        if score >= 70:
            return GroundingLevel.good
        if score >= 50:
            return GroundingLevel.degraded
        if score >= 30:
            return GroundingLevel.poor
        return GroundingLevel.critical
