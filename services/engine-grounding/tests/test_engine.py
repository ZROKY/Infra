"""Tests for the Grounding Engine orchestrator."""

from __future__ import annotations

import pytest

from engine_grounding.engine import GroundingEngine
from engine_grounding.models import (
    GroundingEventInput,
    GroundingLevel,
    RAGContext,
    RetrievedChunk,
)


@pytest.fixture
def engine():
    return GroundingEngine(redis_client=None)


# ── Score-to-Level Mapping ─────────────────────────────────────────────


class TestGroundingLevel:
    def test_excellent(self):
        assert GroundingEngine._score_to_level(95) == GroundingLevel.excellent
        assert GroundingEngine._score_to_level(90) == GroundingLevel.excellent

    def test_good(self):
        assert GroundingEngine._score_to_level(85) == GroundingLevel.good
        assert GroundingEngine._score_to_level(70) == GroundingLevel.good

    def test_degraded(self):
        assert GroundingEngine._score_to_level(60) == GroundingLevel.degraded
        assert GroundingEngine._score_to_level(50) == GroundingLevel.degraded

    def test_poor(self):
        assert GroundingEngine._score_to_level(40) == GroundingLevel.poor
        assert GroundingEngine._score_to_level(30) == GroundingLevel.poor

    def test_critical(self):
        assert GroundingEngine._score_to_level(20) == GroundingLevel.critical
        assert GroundingEngine._score_to_level(0) == GroundingLevel.critical


# ── E2E Engine Tests ───────────────────────────────────────────────────


class TestEngineE2E:
    @pytest.mark.asyncio
    async def test_event_with_rag_context(self, engine):
        event = GroundingEventInput(
            event_id="evt_001",
            client_id="client_abc",
            agent_id="agent_xyz",
            prompt="What is the refund policy?",
            response="Our refund policy allows returns within 30 days of purchase.",
            model="gpt-4o",
            rag_context=RAGContext(
                retrieved_chunks=[
                    RetrievedChunk(id="c1", content="Refund policy: 30 days from purchase date.", score=0.92),
                    RetrievedChunk(id="c2", content="All customers eligible for refunds.", score=0.85),
                    RetrievedChunk(id="c3", content="Contact support to initiate return.", score=0.78),
                ],
                vector_store_type="pinecone",
                retrieval_score=0.92,
                query="What is the refund policy?",
            ),
        )
        result = await engine.analyze(event)
        assert result.event_id == "evt_001"
        assert result.client_id == "client_abc"
        assert result.has_rag_context is True
        assert 0 <= result.grounding_score <= 100
        assert isinstance(result.grounding_level, GroundingLevel)
        assert len(result.evaluations) >= 7  # All 7 evaluators + precision/recall split

    @pytest.mark.asyncio
    async def test_event_without_rag_context(self, engine):
        event = GroundingEventInput(
            event_id="evt_002",
            client_id="client_abc",
            agent_id="agent_xyz",
            prompt="What is 2+2?",
            response="2+2 equals 4.",
            model="gpt-4o",
        )
        result = await engine.analyze(event)
        assert result.event_id == "evt_002"
        assert result.has_rag_context is False
        assert 0 <= result.grounding_score <= 100

    @pytest.mark.asyncio
    async def test_event_with_golden_truth(self, engine):
        event = GroundingEventInput(
            event_id="evt_003",
            client_id="client_abc",
            agent_id="agent_xyz",
            prompt="What is the pricing?",
            response="The pricing is $99 per month.",
            model="gpt-4o",
            ground_truth="Pricing: $99/month for all plans.",
            rag_context=RAGContext(
                retrieved_chunks=[
                    RetrievedChunk(id="c1", content="Pricing: $99/month for all plans.", score=0.95),
                ],
                retrieval_score=0.95,
            ),
        )
        result = await engine.analyze(event)
        # Golden test evaluator should contribute
        golden_eval = next(
            (e for e in result.evaluations if e.evaluation_type.value == "golden_test"), None
        )
        assert golden_eval is not None
        assert golden_eval.score > 0  # Should have some match

    @pytest.mark.asyncio
    async def test_ids_preserved(self, engine):
        event = GroundingEventInput(
            event_id="evt_preserve",
            client_id="cl_test",
            agent_id="ag_test",
            prompt="Test prompt",
            response="Test response",
        )
        result = await engine.analyze(event)
        assert result.event_id == "evt_preserve"
        assert result.client_id == "cl_test"
        assert result.agent_id == "ag_test"

    @pytest.mark.asyncio
    async def test_details_populated(self, engine):
        event = GroundingEventInput(
            event_id="evt_details",
            client_id="cl_d",
            agent_id="ag_d",
            prompt="Tell me about shipping",
            response="We ship worldwide in 3-5 business days.",
            rag_context=RAGContext(
                retrieved_chunks=[
                    RetrievedChunk(id="c1", content="Shipping: worldwide delivery, 3-5 business days.", score=0.9),
                ],
                vector_store_type="weaviate",
                retrieval_score=0.88,
            ),
        )
        result = await engine.analyze(event)
        assert result.details.evaluation_latency_ms >= 0
        assert result.details.vector_db_type == "weaviate"
        assert result.details.ragas_evaluation is not None
        assert result.details.deepeval_evaluation is not None

    @pytest.mark.asyncio
    async def test_score_within_bounds(self, engine):
        """Grounding score must always be 0-100."""
        event = GroundingEventInput(
            event_id="evt_bounds",
            client_id="cl_b",
            agent_id="ag_b",
            prompt="Random question?",
            response="Random answer that has nothing to do with anything at all whatsoever.",
        )
        result = await engine.analyze(event)
        assert 0 <= result.grounding_score <= 100

    @pytest.mark.asyncio
    async def test_low_quality_rag_lowers_score(self, engine):
        """Poor retrieval quality should result in lower grounding score."""
        good_event = GroundingEventInput(
            event_id="evt_good",
            client_id="cl",
            agent_id="ag",
            prompt="What is the refund policy?",
            response="Our refund policy is 30 days.",
            rag_context=RAGContext(
                retrieved_chunks=[
                    RetrievedChunk(id="c1", content="Refund policy: 30 days from purchase.", score=0.95),
                    RetrievedChunk(id="c2", content="All items eligible for return.", score=0.90),
                    RetrievedChunk(id="c3", content="Contact customer service for refunds.", score=0.88),
                ],
                retrieval_score=0.95,
            ),
        )
        bad_event = GroundingEventInput(
            event_id="evt_bad",
            client_id="cl",
            agent_id="ag",
            prompt="What is the refund policy?",
            response="Our refund policy is 30 days.",
            rag_context=RAGContext(
                retrieved_chunks=[
                    RetrievedChunk(id="c1", content="Completely unrelated text about weather.", score=0.2),
                ],
                retrieval_score=0.2,
            ),
        )
        good_result = await engine.analyze(good_event)
        bad_result = await engine.analyze(bad_event)
        assert good_result.grounding_score > bad_result.grounding_score
