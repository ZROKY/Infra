"""Pydantic models for the System Engine."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────


class SystemHealthLevel(StrEnum):
    optimal = "optimal"  # 90-100
    healthy = "healthy"  # 70-89
    degraded = "degraded"  # 50-69
    unhealthy = "unhealthy"  # 30-49
    critical = "critical"  # 0-29


class MonitorType(StrEnum):
    latency = "latency"
    error_rate = "error_rate"
    cost = "cost"
    uptime = "uptime"
    throughput = "throughput"
    cost_per_outcome = "cost_per_outcome"
    performance_quality_correlation = "performance_quality_correlation"


# ── Input Models ───────────────────────────────────────────────────────


class SystemEventInput(BaseModel):
    event_id: str = ""
    client_id: str = ""
    agent_id: str = ""
    session_id: str = ""
    prompt: str = ""
    response: str = ""
    model: str = ""
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    status_code: int = 200
    is_error: bool = False
    error_type: str = ""
    cost_usd: float = 0.0
    quality_score: float = 0.0  # from grounding/safety engines
    metadata: dict = Field(default_factory=dict)


# ── Monitor Result Models ─────────────────────────────────────────────


class MonitorResult(BaseModel):
    monitor_type: MonitorType
    score: float = 0.0  # 0-100
    confidence: float = 1.0
    threshold_exceeded: bool = False
    details: dict = Field(default_factory=dict)


class LatencyMetrics(BaseModel):
    p50_ms: int = 0
    p95_ms: int = 0
    p99_ms: int = 0
    avg_ms: int = 0
    min_ms: int = 0
    max_ms: int = 0


class CostMetrics(BaseModel):
    event_cost_usd: float = 0.0
    daily_total_usd: float = 0.0
    monthly_total_usd: float = 0.0
    daily_budget_pct: float = 0.0
    monthly_budget_pct: float = 0.0
    cost_per_1k_tokens: float = 0.0


class ThroughputMetrics(BaseModel):
    current_rps: float = 0.0
    capacity_utilization_pct: float = 0.0
    peak_rps_today: float = 0.0


class SystemDetails(BaseModel):
    latency_score: float = 0.0
    error_score: float = 0.0
    cost_score: float = 0.0
    uptime_score: float = 0.0
    throughput_score: float = 0.0
    latency_metrics: LatencyMetrics = Field(default_factory=LatencyMetrics)
    cost_metrics: CostMetrics = Field(default_factory=CostMetrics)
    throughput_metrics: ThroughputMetrics = Field(default_factory=ThroughputMetrics)
    uptime_pct: float = 100.0
    error_rate_pct: float = 0.0
    waste_ratio: float = 0.0
    perf_quality_correlation: float = 0.0
    evaluation_latency_ms: int = 0


# ── Engine Output ──────────────────────────────────────────────────────


class SystemEngineResult(BaseModel):
    event_id: str = ""
    client_id: str = ""
    agent_id: str = ""
    system_score: float = 0.0  # 0-100
    system_level: SystemHealthLevel = SystemHealthLevel.healthy
    monitors: list[MonitorResult] = Field(default_factory=list)
    details: SystemDetails = Field(default_factory=SystemDetails)
