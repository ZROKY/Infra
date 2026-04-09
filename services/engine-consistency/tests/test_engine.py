"""Tests for Consistency Engine orchestrator."""

from __future__ import annotations

import pytest

from engine_consistency.engine import ConsistencyEngine
from engine_consistency.models import ConsistencyEventInput, ConsistencyLevel


class TestConsistencyEngine:
    @pytest.fixture
    def engine(self):
        return ConsistencyEngine(redis_client=None)

    @pytest.fixture
    def sample_event(self):
        return ConsistencyEventInput(
            event_id="evt-001",
            client_id="client-1",
            agent_id="agent-1",
            prompt="What is the capital of France?",
            response="The capital of France is Paris. It is known as the City of Light and is famous for the Eiffel Tower, the Louvre Museum, and Notre-Dame Cathedral.",
            model="gpt-4",
            model_version_str="gpt-4-0125",
        )

    @pytest.mark.asyncio
    async def test_analyze_returns_result(self, engine, sample_event):
        result = await engine.analyze(sample_event)
        assert result.event_id == "evt-001"
        assert result.client_id == "client-1"
        assert 0 <= result.consistency_score <= 100
        assert result.consistency_level in list(ConsistencyLevel)
        assert len(result.analyses) > 0

    @pytest.mark.asyncio
    async def test_details_populated(self, engine, sample_event):
        result = await engine.analyze(sample_event)
        assert result.details.benchmark_score >= 0
        assert result.details.model_version == "gpt-4-0125"
        assert result.details.evaluation_latency_ms >= 0

    @pytest.mark.asyncio
    async def test_empty_response_scores_lower(self, engine):
        event = ConsistencyEventInput(
            event_id="evt-002",
            client_id="client-1",
            agent_id="agent-1",
            prompt="Tell me about Python",
            response="",
            model="gpt-4",
        )
        result = await engine.analyze(event)
        assert result.consistency_score < 80

    @pytest.mark.asyncio
    async def test_score_to_level_stable(self, engine):
        assert engine._score_to_level(95) == ConsistencyLevel.stable

    @pytest.mark.asyncio
    async def test_score_to_level_nominal(self, engine):
        assert engine._score_to_level(75) == ConsistencyLevel.nominal

    @pytest.mark.asyncio
    async def test_score_to_level_degraded(self, engine):
        assert engine._score_to_level(55) == ConsistencyLevel.degraded

    @pytest.mark.asyncio
    async def test_score_to_level_unstable(self, engine):
        assert engine._score_to_level(35) == ConsistencyLevel.unstable

    @pytest.mark.asyncio
    async def test_score_to_level_critical(self, engine):
        assert engine._score_to_level(15) == ConsistencyLevel.critical

    @pytest.mark.asyncio
    async def test_multiple_analyses_in_result(self, engine, sample_event):
        result = await engine.analyze(sample_event)
        # Should have: 1 benchmark + 1 regression + N drift + 1 fingerprint + 1 version
        assert len(result.analyses) >= 5
