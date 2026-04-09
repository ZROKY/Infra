"""Tests for System Engine orchestrator."""

from __future__ import annotations

import pytest

from engine_system.engine import SystemEngine
from engine_system.models import SystemEventInput, SystemHealthLevel


class TestSystemEngine:
    @pytest.fixture
    def engine(self):
        return SystemEngine(redis_client=None)

    @pytest.fixture
    def healthy_event(self):
        return SystemEventInput(
            event_id="evt-001",
            client_id="client-1",
            agent_id="agent-1",
            prompt="What is Python?",
            response="Python is a programming language.",
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            latency_ms=500,
            status_code=200,
            is_error=False,
            cost_usd=0.001,
            quality_score=85.0,
        )

    @pytest.fixture
    def unhealthy_event(self):
        return SystemEventInput(
            event_id="evt-002",
            client_id="client-1",
            agent_id="agent-1",
            latency_ms=10000,
            status_code=500,
            is_error=True,
            cost_usd=0.05,
            quality_score=20.0,
        )

    @pytest.mark.asyncio
    async def test_healthy_event_good_score(self, engine, healthy_event):
        result = await engine.analyze(healthy_event)
        assert result.event_id == "evt-001"
        assert result.system_score >= 70
        assert result.system_level in (SystemHealthLevel.optimal, SystemHealthLevel.healthy)
        assert len(result.monitors) == 7

    @pytest.mark.asyncio
    async def test_unhealthy_event_lower_score(self, engine, unhealthy_event):
        result = await engine.analyze(unhealthy_event)
        assert result.system_score < 80

    @pytest.mark.asyncio
    async def test_details_populated(self, engine, healthy_event):
        result = await engine.analyze(healthy_event)
        assert result.details.latency_score >= 0
        assert result.details.error_score >= 0
        assert result.details.cost_score >= 0
        assert result.details.uptime_score >= 0
        assert result.details.throughput_score >= 0
        assert result.details.evaluation_latency_ms >= 0

    @pytest.mark.asyncio
    async def test_score_to_level_optimal(self, engine):
        assert engine._score_to_level(95) == SystemHealthLevel.optimal

    @pytest.mark.asyncio
    async def test_score_to_level_healthy(self, engine):
        assert engine._score_to_level(75) == SystemHealthLevel.healthy

    @pytest.mark.asyncio
    async def test_score_to_level_degraded(self, engine):
        assert engine._score_to_level(55) == SystemHealthLevel.degraded

    @pytest.mark.asyncio
    async def test_score_to_level_unhealthy(self, engine):
        assert engine._score_to_level(35) == SystemHealthLevel.unhealthy

    @pytest.mark.asyncio
    async def test_score_to_level_critical(self, engine):
        assert engine._score_to_level(15) == SystemHealthLevel.critical

    @pytest.mark.asyncio
    async def test_all_monitor_types_present(self, engine, healthy_event):
        result = await engine.analyze(healthy_event)
        monitor_types = {m.monitor_type for m in result.monitors}
        assert "latency" in monitor_types
        assert "error_rate" in monitor_types
        assert "cost" in monitor_types
        assert "uptime" in monitor_types
        assert "throughput" in monitor_types
        assert "cost_per_outcome" in monitor_types
        assert "performance_quality_correlation" in monitor_types
