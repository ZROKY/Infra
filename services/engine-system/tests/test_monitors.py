"""Tests for System Engine monitors."""

from __future__ import annotations

import pytest

from engine_system.models import MonitorType
from engine_system.monitors.cost import CostMonitor
from engine_system.monitors.cost_per_outcome import CostPerOutcomeMonitor
from engine_system.monitors.error_rate import ErrorRateMonitor
from engine_system.monitors.latency import LatencyMonitor
from engine_system.monitors.perf_quality import PerfQualityMonitor
from engine_system.monitors.throughput import ThroughputMonitor
from engine_system.monitors.uptime import UptimeMonitor

# ── Latency Monitor ───────────────────────────────────────────────────


class TestLatencyMonitor:
    @pytest.fixture
    def monitor(self):
        return LatencyMonitor(redis_client=None)

    @pytest.mark.asyncio
    async def test_low_latency_high_score(self, monitor):
        result, metrics = await monitor.analyze(200, "c1", "a1")
        assert result.monitor_type == MonitorType.latency
        assert result.score >= 90

    @pytest.mark.asyncio
    async def test_high_latency_low_score(self, monitor):
        result, metrics = await monitor.analyze(10000, "c1", "a1")
        assert result.score < 50

    @pytest.mark.asyncio
    async def test_metrics_populated(self, monitor):
        result, metrics = await monitor.analyze(500, "c1", "a1")
        assert metrics.p50_ms > 0


# ── Error Rate Monitor ────────────────────────────────────────────────


class TestErrorRateMonitor:
    @pytest.fixture
    def monitor(self):
        return ErrorRateMonitor(redis_client=None)

    @pytest.mark.asyncio
    async def test_no_error_high_score(self, monitor):
        result = await monitor.analyze(200, False, "c1", "a1")
        assert result.monitor_type == MonitorType.error_rate
        assert result.score >= 90

    @pytest.mark.asyncio
    async def test_error_lower_score(self, monitor):
        result = await monitor.analyze(500, True, "c1", "a1")
        assert result.score < 100


# ── Cost Monitor ──────────────────────────────────────────────────────


class TestCostMonitor:
    @pytest.fixture
    def monitor(self):
        return CostMonitor(redis_client=None)

    @pytest.mark.asyncio
    async def test_low_cost_high_score(self, monitor):
        result, metrics = await monitor.analyze(0.001, 100, 50, "c1", "a1")
        assert result.monitor_type == MonitorType.cost
        assert result.score >= 90

    @pytest.mark.asyncio
    async def test_metrics_populated(self, monitor):
        result, metrics = await monitor.analyze(0.005, 200, 100, "c1", "a1")
        assert metrics.event_cost_usd == 0.005
        assert metrics.cost_per_1k_tokens > 0


# ── Uptime Monitor ────────────────────────────────────────────────────


class TestUptimeMonitor:
    @pytest.fixture
    def monitor(self):
        return UptimeMonitor(redis_client=None)

    @pytest.mark.asyncio
    async def test_success_high_score(self, monitor):
        result = await monitor.analyze(False, "c1", "a1")
        assert result.monitor_type == MonitorType.uptime
        assert result.score >= 90

    @pytest.mark.asyncio
    async def test_error_lower_score(self, monitor):
        result = await monitor.analyze(True, "c1", "a1")
        assert result.score < 80


# ── Throughput Monitor ────────────────────────────────────────────────


class TestThroughputMonitor:
    @pytest.fixture
    def monitor(self):
        return ThroughputMonitor(redis_client=None)

    @pytest.mark.asyncio
    async def test_returns_result_and_metrics(self, monitor):
        result, metrics = await monitor.analyze("c1", "a1")
        assert result.monitor_type == MonitorType.throughput
        assert result.score >= 0


# ── Cost Per Outcome Monitor ──────────────────────────────────────────


class TestCostPerOutcomeMonitor:
    @pytest.fixture
    def monitor(self):
        return CostPerOutcomeMonitor(redis_client=None)

    @pytest.mark.asyncio
    async def test_success_high_score(self, monitor):
        result = await monitor.analyze(0.01, 85.0, False, "c1", "a1")
        assert result.monitor_type == MonitorType.cost_per_outcome
        assert result.score >= 80

    @pytest.mark.asyncio
    async def test_error_wasted(self, monitor):
        result = await monitor.analyze(0.01, 30.0, True, "c1", "a1")
        # With no Redis, totals are 0 so single wasted event = 100% waste
        assert result.threshold_exceeded


# ── Perf Quality Correlation Monitor ──────────────────────────────────


class TestPerfQualityMonitor:
    @pytest.fixture
    def monitor(self):
        return PerfQualityMonitor(redis_client=None)

    @pytest.mark.asyncio
    async def test_insufficient_data(self, monitor):
        result = await monitor.analyze(500, 80.0, "c1", "a1")
        assert result.monitor_type == MonitorType.performance_quality_correlation
        assert result.score == 85.0
        assert result.details["reason"] == "insufficient_data"
