"""Tests for Trust Score Computer — formula, overrides, cold-start, coverage."""

from __future__ import annotations

import pytest

from trust_computer.coverage import CoverageCalculator
from trust_computer.engine import TrustScoreEngine
from trust_computer.models import (
    ColdStartLabel,
    CoverageBand,
    EngineScores,
    TrustScoreInput,
    TrustStatus,
)

# ── Coverage Calculator ────────────────────────────────────────────────


class TestCoverageCalculator:
    @pytest.fixture
    def calc(self):
        return CoverageCalculator(redis_client=None)

    def test_full_coverage(self, calc):
        result = calc.compute(1000, 1000, "c1", "a1")
        assert result.score == 100.0
        assert result.band == CoverageBand.full_coverage

    def test_partial_coverage(self, calc):
        result = calc.compute(600, 1000, "c1", "a1")
        assert result.score == 60.0
        assert result.band == CoverageBand.partial_coverage

    def test_low_coverage(self, calc):
        result = calc.compute(200, 1000, "c1", "a1")
        assert result.score == 20.0
        assert result.band == CoverageBand.low_coverage

    def test_over_100_capped(self, calc):
        result = calc.compute(1500, 1000, "c1", "a1")
        assert result.score == 100.0

    def test_no_expected_no_redis(self, calc):
        result = calc.compute(500, 0, "c1", "a1")
        # No Redis, no history → default 50
        assert result.score == 50.0


# ── Trust Score Engine — Formula Verification ──────────────────────────


class TestTrustScoreFormula:
    @pytest.fixture
    def engine(self):
        return TrustScoreEngine(redis_client=None)

    def test_perfect_scores(self, engine):
        """All 100 → Trust Score = 100 (with coverage at 100)."""
        result = engine.compute(TrustScoreInput(
            client_id="c1",
            agent_id="a1",
            engine_scores=EngineScores(
                safety_score=100, grounding_score=100,
                consistency_score=100, system_score=100,
            ),
            events_received_24h=1000,
            expected_daily_events=1000,
            total_events=500,
        ))
        assert result.score == 100.0
        assert result.status == TrustStatus.trusted

    def test_manual_weighted_calculation(self, engine):
        """Verify formula: 0.30×S + 0.25×G + 0.20×C + 0.10×Sys + 0.15×Coverage."""
        result = engine.compute(TrustScoreInput(
            client_id="c1",
            agent_id="a1",
            engine_scores=EngineScores(
                safety_score=90, grounding_score=80,
                consistency_score=70, system_score=60,
            ),
            events_received_24h=800,
            expected_daily_events=1000,
            total_events=500,
        ))
        # Coverage = 80%, score = 80.0
        # 0.30×90 + 0.25×80 + 0.20×70 + 0.10×60 + 0.15×80
        # = 27 + 20 + 14 + 6 + 12 = 79.0
        assert result.score == 79.0
        assert result.status == TrustStatus.caution

    def test_zero_scores(self, engine):
        """All 0 → Trust Score near 0 (coverage at 0 without Redis gives 50)."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=0, grounding_score=0,
                consistency_score=0, system_score=0,
            ),
            events_received_24h=0, expected_daily_events=1000,
            total_events=500,
        ))
        # Coverage = 0/1000 = 0, but safety < 40 cap applies too
        assert result.score <= 50


# ── Trust Score Engine — Override Rules ────────────────────────────────


class TestOverrideRules:
    @pytest.fixture
    def engine(self):
        return TrustScoreEngine(redis_client=None)

    def test_safety_floor_caps_at_50(self, engine):
        """RULE 1: Safety < 40 → Trust Score CANNOT exceed 50."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=30,  # Below 40 threshold
                grounding_score=100, consistency_score=100, system_score=100,
            ),
            events_received_24h=1000, expected_daily_events=1000,
            total_events=500,
        ))
        assert result.score <= 50.0
        assert result.overrides.safety_floor_active

    def test_safety_above_threshold_no_cap(self, engine):
        """Safety ≥ 40 → no floor applied."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=50, grounding_score=80,
                consistency_score=80, system_score=80,
            ),
            events_received_24h=1000, expected_daily_events=1000,
            total_events=500,
        ))
        assert not result.overrides.safety_floor_active
        assert result.score > 50

    def test_critical_incident_penalty(self, engine):
        """RULE 2: Critical incident → -15 points."""
        result_normal = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=90, grounding_score=80,
                consistency_score=80, system_score=80,
            ),
            events_received_24h=1000, expected_daily_events=1000,
            total_events=500, has_critical_incident=False,
        ))
        result_incident = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=90, grounding_score=80,
                consistency_score=80, system_score=80,
            ),
            events_received_24h=1000, expected_daily_events=1000,
            total_events=500, has_critical_incident=True,
        ))
        assert result_incident.score == result_normal.score - 15
        assert result_incident.overrides.critical_incident_active
        assert result_incident.overrides.penalty_applied == 15

    def test_system_down_returns_unavailable(self, engine):
        """RULE 3: Endpoint unreachable → UNAVAILABLE."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=90, grounding_score=80,
                consistency_score=80, system_score=80,
            ),
            total_events=500, system_endpoint_reachable=False,
        ))
        assert result.score is None
        assert result.status == TrustStatus.unavailable
        assert result.overrides.system_down_active

    def test_low_coverage_caveat(self, engine):
        """RULE 4: Coverage < 50 → caveat displayed."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=90, grounding_score=80,
                consistency_score=80, system_score=80,
            ),
            events_received_24h=100, expected_daily_events=1000,
            total_events=500,
        ))
        assert result.overrides.low_coverage_caveat
        assert "Low coverage" in result.overrides.details[0]

    def test_safety_floor_and_critical_combined(self, engine):
        """Safety floor + critical incident can stack."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=20, grounding_score=100,
                consistency_score=100, system_score=100,
            ),
            events_received_24h=1000, expected_daily_events=1000,
            total_events=500, has_critical_incident=True,
        ))
        # Floor caps at 50, then -15 for incident = 35
        assert result.score == 35.0
        assert result.overrides.safety_floor_active
        assert result.overrides.critical_incident_active


# ── Cold-Start Handling ────────────────────────────────────────────────


class TestColdStart:
    @pytest.fixture
    def engine(self):
        return TrustScoreEngine(redis_client=None)

    def test_collecting_no_score(self, engine):
        """0-9 events → no score."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=90, grounding_score=80,
                consistency_score=80, system_score=80,
            ),
            total_events=5,
        ))
        assert result.score is None
        assert result.cold_start_label == ColdStartLabel.collecting

    def test_provisional(self, engine):
        """10-99 events → PROVISIONAL, score computed."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=90, grounding_score=80,
                consistency_score=80, system_score=80,
            ),
            events_received_24h=1000, expected_daily_events=1000,
            total_events=50,
        ))
        assert result.score is not None
        assert result.cold_start_label == ColdStartLabel.provisional

    def test_building(self, engine):
        """100-499 events → BUILDING."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=90, grounding_score=80,
                consistency_score=80, system_score=80,
            ),
            events_received_24h=1000, expected_daily_events=1000,
            total_events=200,
        ))
        assert result.cold_start_label == ColdStartLabel.building

    def test_stable(self, engine):
        """500+ events → STABLE."""
        result = engine.compute(TrustScoreInput(
            client_id="c1", agent_id="a1",
            engine_scores=EngineScores(
                safety_score=90, grounding_score=80,
                consistency_score=80, system_score=80,
            ),
            events_received_24h=1000, expected_daily_events=1000,
            total_events=1000,
        ))
        assert result.cold_start_label == ColdStartLabel.stable


# ── Status Bands ──────────────────────────────────────────────────────


class TestStatusBands:
    @pytest.fixture
    def engine(self):
        return TrustScoreEngine(redis_client=None)

    def test_trusted_band(self, engine):
        assert engine._score_to_status(95) == TrustStatus.trusted
        assert engine._score_to_status(90) == TrustStatus.trusted

    def test_caution_band(self, engine):
        assert engine._score_to_status(80) == TrustStatus.caution
        assert engine._score_to_status(75) == TrustStatus.caution

    def test_at_risk_band(self, engine):
        assert engine._score_to_status(70) == TrustStatus.at_risk
        assert engine._score_to_status(60) == TrustStatus.at_risk

    def test_critical_band(self, engine):
        assert engine._score_to_status(59) == TrustStatus.critical
        assert engine._score_to_status(0) == TrustStatus.critical
