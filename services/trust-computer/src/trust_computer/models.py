"""Pydantic models for the Trust Score Computer."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────


class TrustStatus(StrEnum):
    trusted = "trusted"  # 90-100  🟢
    caution = "caution"  # 75-89   🟡
    at_risk = "at_risk"  # 60-74   🟠
    critical = "critical"  # 0-59  🔴
    unavailable = "unavailable"  # System down


class ColdStartLabel(StrEnum):
    collecting = "collecting"  # 0-9 events — no score yet
    provisional = "provisional"  # 10-99 events
    building = "building"  # 100-499 events
    stable = "stable"  # 500+ events


class CoverageBand(StrEnum):
    full_coverage = "full_coverage"  # ≥80%
    partial_coverage = "partial_coverage"  # 50-79%
    low_coverage = "low_coverage"  # <50%


# ── Engine Score Inputs ────────────────────────────────────────────────


class EngineScores(BaseModel):
    safety_score: float = 0.0
    grounding_score: float = 0.0
    consistency_score: float = 0.0
    system_score: float = 0.0


class CoverageInfo(BaseModel):
    score: float = 0.0  # 0-100
    band: CoverageBand = CoverageBand.low_coverage
    events_received_24h: int = 0
    expected_daily_events: int = 0


class OverrideInfo(BaseModel):
    safety_floor_active: bool = False
    critical_incident_active: bool = False
    system_down_active: bool = False
    low_coverage_caveat: bool = False
    penalty_applied: float = 0.0
    details: list[str] = Field(default_factory=list)


# ── Trust Score Computation Input ──────────────────────────────────────


class TrustScoreInput(BaseModel):
    client_id: str = ""
    agent_id: str = ""
    engine_scores: EngineScores = Field(default_factory=EngineScores)
    events_received_24h: int = 0
    expected_daily_events: int = 0
    total_events: int = 0
    has_critical_incident: bool = False
    system_endpoint_reachable: bool = True


# ── Trust Score Output ─────────────────────────────────────────────────


class TrustScoreResult(BaseModel):
    client_id: str = ""
    agent_id: str = ""
    score: float | None = None  # None when collecting / unavailable
    status: TrustStatus = TrustStatus.caution
    cold_start_label: ColdStartLabel = ColdStartLabel.collecting
    engines: EngineScores = Field(default_factory=EngineScores)
    coverage: CoverageInfo = Field(default_factory=CoverageInfo)
    overrides: OverrideInfo = Field(default_factory=OverrideInfo)
    events_received_24h: int = 0
    formula_breakdown: dict = Field(default_factory=dict)
