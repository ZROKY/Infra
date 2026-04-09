"""Pydantic models for the Consistency Engine."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────


class ConsistencyLevel(StrEnum):
    stable = "stable"  # 90-100
    nominal = "nominal"  # 70-89
    degraded = "degraded"  # 50-69
    unstable = "unstable"  # 30-49
    critical = "critical"  # 0-29


class AnalysisType(StrEnum):
    benchmark = "benchmark"
    regression = "regression"
    drift_psi = "drift_psi"
    drift_kl = "drift_kl"
    drift_wasserstein = "drift_wasserstein"
    drift_js = "drift_js"
    fingerprint = "fingerprint"
    version_tracking = "version_tracking"


# ── Input Models ───────────────────────────────────────────────────────


class ConsistencyEventInput(BaseModel):
    event_id: str = ""
    client_id: str = ""
    agent_id: str = ""
    session_id: str = ""
    prompt: str = ""
    response: str = ""
    model: str = ""
    model_version_str: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    metadata: dict = Field(default_factory=dict)


# ── Analysis Result Models ─────────────────────────────────────────────


class AnalysisResult(BaseModel):
    analysis_type: AnalysisType
    score: float = 0.0  # 0-100
    confidence: float = 1.0  # 0-1
    threshold_exceeded: bool = False
    details: dict = Field(default_factory=dict)


class DriftMetrics(BaseModel):
    psi: float = 0.0
    kl_divergence: float = 0.0
    wasserstein: float = 0.0
    js_divergence: float = 0.0
    drift_detected: bool = False


class ConsistencyDetails(BaseModel):
    benchmark_score: float = 0.0
    regression_test_score: float = 0.0
    drift_metrics: DriftMetrics = Field(default_factory=DriftMetrics)
    fingerprint_delta: float = 0.0
    model_version: str = ""
    model_version_changed: bool = False
    drift_detected: bool = False
    drift_magnitude: float = 0.0
    trend_7day_avg: float = 0.0
    evaluation_latency_ms: int = 0


# ── Engine Output ──────────────────────────────────────────────────────


class ConsistencyEngineResult(BaseModel):
    event_id: str = ""
    client_id: str = ""
    agent_id: str = ""
    consistency_score: float = 0.0  # 0-100
    consistency_level: ConsistencyLevel = ConsistencyLevel.nominal
    analyses: list[AnalysisResult] = Field(default_factory=list)
    details: ConsistencyDetails = Field(default_factory=ConsistencyDetails)
