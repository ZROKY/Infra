"""Tests for all grounding evaluators."""

from __future__ import annotations

import pytest

from engine_grounding.evaluators.consistency import ConsistencyEvaluator
from engine_grounding.evaluators.faithfulness import FaithfulnessEvaluator
from engine_grounding.evaluators.golden_tests import GoldenTestEvaluator
from engine_grounding.evaluators.hallucination import HallucinationEvaluator
from engine_grounding.evaluators.retrieval_quality import RetrievalQualityEvaluator
from engine_grounding.models import EvaluationType, RAGContext, RetrievedChunk

# ── Faithfulness ───────────────────────────────────────────────────────


class TestFaithfulness:
    @pytest.mark.asyncio
    async def test_no_source_chunks(self):
        ev = FaithfulnessEvaluator()
        result = await ev.evaluate("The price is $99.", [])
        assert result.evaluation_type == EvaluationType.faithfulness
        assert result.score == 50.0
        assert result.confidence == 0.3

    @pytest.mark.asyncio
    async def test_heuristic_high_overlap(self):
        ev = FaithfulnessEvaluator()
        response = "The refund policy allows returns within 30 days of purchase."
        sources = ["Refund policy: returns within 30 days of purchase date."]
        # LLM judge will fail (no server), fallback to heuristic
        result = await ev.evaluate(response, sources)
        assert result.evaluation_type == EvaluationType.faithfulness
        assert result.score > 40  # High word overlap should score well

    @pytest.mark.asyncio
    async def test_heuristic_low_overlap(self):
        ev = FaithfulnessEvaluator()
        response = "We donate a million dollars to charity every year."
        sources = ["Pricing: $99/month. Shipping: $5 flat rate."]
        result = await ev.evaluate(response, sources)
        assert result.score < 60  # Low overlap → low score

    @pytest.mark.asyncio
    async def test_empty_response(self):
        ev = FaithfulnessEvaluator()
        result = await ev.evaluate("", ["Some source content"])
        # Empty response → heuristic returns low confidence
        assert result.evaluation_type == EvaluationType.faithfulness

    def test_parse_json_array(self):
        ev = FaithfulnessEvaluator()
        assert ev._parse_json_array('["a", "b"]') == ["a", "b"]
        assert ev._parse_json_array('```json\n["x"]\n```') == ["x"]
        assert ev._parse_json_array("garbage") == []


# ── Hallucination ──────────────────────────────────────────────────────


class TestHallucination:
    @pytest.mark.asyncio
    async def test_with_high_overlap(self):
        ev = HallucinationEvaluator()
        response = "Pricing is $99 per month. All plans included."
        sources = ["Pricing is $99 per month. All plans included."]
        result = await ev.evaluate("pricing?", response, sources)
        assert result.evaluation_type == EvaluationType.hallucination
        assert result.score > 30  # High overlap → low hallucination

    @pytest.mark.asyncio
    async def test_with_low_overlap(self):
        ev = HallucinationEvaluator()
        response = "We are the biggest company in the world with offices on Mars."
        sources = ["Small startup founded in 2024."]
        result = await ev.evaluate("tell me about the company", response, sources)
        assert result.score < 60  # Low overlap → high hallucination → low score

    @pytest.mark.asyncio
    async def test_without_context(self):
        ev = HallucinationEvaluator()
        result = await ev.evaluate("What is 2+2?", "2+2 equals 4.", [])
        assert result.evaluation_type == EvaluationType.hallucination
        # Without context, defaults to moderate confidence
        assert 0 <= result.score <= 100

    @pytest.mark.asyncio
    async def test_heuristic_empty_response(self):
        result = HallucinationEvaluator._heuristic_hallucination("", ["source text"])
        assert result.score == 50.0
        assert result.confidence == 0.2


# ── Retrieval Quality ──────────────────────────────────────────────────


class TestRetrievalQuality:
    @pytest.mark.asyncio
    async def test_no_rag_context(self):
        ev = RetrievalQualityEvaluator()
        result = await ev.evaluate(None)
        assert result.evaluation_type == EvaluationType.retrieval_quality
        assert result.score == 50.0
        assert result.details.get("skipped") is True

    @pytest.mark.asyncio
    async def test_high_retrieval_score(self):
        ev = RetrievalQualityEvaluator()
        ctx = RAGContext(
            retrieved_chunks=[
                RetrievedChunk(id="c1", content="Refund policy info", score=0.95),
                RetrievedChunk(id="c2", content="Return process", score=0.88),
                RetrievedChunk(id="c3", content="FAQ about returns", score=0.82),
            ],
            vector_store_type="pinecone",
            retrieval_score=0.92,
        )
        result = await ev.evaluate(ctx)
        assert result.score > 75  # Good scores should produce high result
        assert result.details["health"] == "healthy"
        assert result.details["vector_db_type"] == "pinecone"

    @pytest.mark.asyncio
    async def test_low_retrieval_score(self):
        ev = RetrievalQualityEvaluator()
        ctx = RAGContext(
            retrieved_chunks=[
                RetrievedChunk(id="c1", content="Unrelated content", score=0.3),
            ],
            vector_store_type="qdrant",
            retrieval_score=0.35,
        )
        result = await ev.evaluate(ctx)
        assert result.score < 60

    @pytest.mark.asyncio
    async def test_empty_chunks(self):
        ev = RetrievalQualityEvaluator()
        ctx = RAGContext(
            retrieved_chunks=[
                RetrievedChunk(id="c1", content="", score=0.9),
                RetrievedChunk(id="c2", content="has content", score=0.9),
            ],
            retrieval_score=0.9,
        )
        result = await ev.evaluate(ctx)
        # 50% content ratio should reduce score
        assert result.details["non_empty_chunks"] == 1

    @pytest.mark.asyncio
    async def test_optimal_chunk_count(self):
        ev = RetrievalQualityEvaluator()
        ctx = RAGContext(
            retrieved_chunks=[
                RetrievedChunk(id=f"c{i}", content=f"Content {i}", score=0.85)
                for i in range(5)
            ],
            retrieval_score=0.85,
        )
        result = await ev.evaluate(ctx)
        assert result.score > 70  # 5 chunks is in the optimal 3-8 range


# ── Golden Tests ───────────────────────────────────────────────────────


class TestGoldenTests:
    @pytest.mark.asyncio
    async def test_no_ground_truth(self):
        ev = GoldenTestEvaluator()
        result = await ev.evaluate("Some response", None)
        assert result.evaluation_type == EvaluationType.golden_test
        assert result.confidence == 0.0
        assert result.details.get("skipped") is True

    @pytest.mark.asyncio
    async def test_heuristic_high_similarity(self):
        ev = GoldenTestEvaluator()
        # LLM unavailable → falls back to Jaccard
        result = await ev.evaluate(
            "Our refund policy allows returns within 30 days.",
            "Refund policy: 30 day return window.",
        )
        assert result.evaluation_type == EvaluationType.golden_test
        assert result.score > 30  # Shared terms: refund, policy, 30, days, return

    @pytest.mark.asyncio
    async def test_heuristic_low_similarity(self):
        ev = GoldenTestEvaluator()
        result = await ev.evaluate(
            "The sky is blue and the grass is green.",
            "Our quarterly revenue exceeded expectations by 20%.",
        )
        assert result.score < 30  # Very different content


# ── Consistency ────────────────────────────────────────────────────────


class TestConsistency:
    @pytest.mark.asyncio
    async def test_empty_response(self):
        ev = ConsistencyEvaluator()
        result = await ev.evaluate("question?", "")
        assert result.evaluation_type == EvaluationType.consistency
        assert result.score == 50.0

    @pytest.mark.asyncio
    async def test_heuristic_no_contradictions(self):
        result = ConsistencyEvaluator._heuristic_consistency(
            "The refund policy is 30 days. All customers are eligible. Contact support to start."
        )
        assert result.score == 90.0

    @pytest.mark.asyncio
    async def test_heuristic_with_contradiction(self):
        result = ConsistencyEvaluator._heuristic_consistency(
            "The price is $99. The product is available. The price is not $99."
        )
        assert result.score < 90.0  # Should detect is / is not contradiction
