"""Trust Score aggregation engine — weighted formula + override rules + cold-start handling.

V1 Trust Score Formula:
    0.30 × Safety + 0.25 × Grounding + 0.20 × Consistency + 0.10 × System + 0.15 × Coverage

Override Rules:
  1. Safety Floor: Safety < 40 → Trust Score CANNOT exceed 50
  2. Critical Incident: Any CRITICAL incident → Trust Score drops min 15 pts
  3. System Down: Endpoint unreachable → Trust Score = UNAVAILABLE
  4. Low Coverage: Coverage < 50 → Score displayed WITH caveat
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import settings
from .coverage import CoverageCalculator
from .models import (
    ColdStartLabel,
    OverrideInfo,
    TrustScoreInput,
    TrustScoreResult,
    TrustStatus,
)

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class TrustScoreEngine:
    """Compute the unified Trust Score from all engine scores."""

    def __init__(self, redis_client: Redis | None = None):
        self.coverage_calc = CoverageCalculator(redis_client=redis_client)

    def compute(self, input_data: TrustScoreInput) -> TrustScoreResult:
        """Full pipeline: cold-start → coverage → formula → overrides → status."""

        # ── 1. Cold-start check ────────────────────────────────────────
        cold_start_label = self._cold_start_label(input_data.total_events)

        if cold_start_label == ColdStartLabel.collecting:
            return TrustScoreResult(
                client_id=input_data.client_id,
                agent_id=input_data.agent_id,
                score=None,
                status=TrustStatus.caution,
                cold_start_label=cold_start_label,
                engines=input_data.engine_scores,
                events_received_24h=input_data.events_received_24h,
                formula_breakdown={"reason": "collecting_data"},
            )

        # ── 2. System down check (RULE 3) ─────────────────────────────
        if not input_data.system_endpoint_reachable:
            return TrustScoreResult(
                client_id=input_data.client_id,
                agent_id=input_data.agent_id,
                score=None,
                status=TrustStatus.unavailable,
                cold_start_label=cold_start_label,
                engines=input_data.engine_scores,
                overrides=OverrideInfo(
                    system_down_active=True,
                    details=["System endpoint unreachable — Trust Score UNAVAILABLE"],
                ),
                events_received_24h=input_data.events_received_24h,
                formula_breakdown={"reason": "system_down"},
            )

        # ── 3. Coverage score ──────────────────────────────────────────
        coverage = self.coverage_calc.compute(
            input_data.events_received_24h,
            input_data.expected_daily_events,
            input_data.client_id,
            input_data.agent_id,
        )

        # ── 4. Weighted formula ────────────────────────────────────────
        es = input_data.engine_scores

        safety_contrib = settings.weight_safety * es.safety_score
        grounding_contrib = settings.weight_grounding * es.grounding_score
        consistency_contrib = settings.weight_consistency * es.consistency_score
        system_contrib = settings.weight_system * es.system_score
        coverage_contrib = settings.weight_coverage * coverage.score

        raw_score = (
            safety_contrib
            + grounding_contrib
            + consistency_contrib
            + system_contrib
            + coverage_contrib
        )

        formula_breakdown = {
            "safety": {"weight": settings.weight_safety, "score": es.safety_score, "contribution": round(safety_contrib, 2)},
            "grounding": {"weight": settings.weight_grounding, "score": es.grounding_score, "contribution": round(grounding_contrib, 2)},
            "consistency": {"weight": settings.weight_consistency, "score": es.consistency_score, "contribution": round(consistency_contrib, 2)},
            "system": {"weight": settings.weight_system, "score": es.system_score, "contribution": round(system_contrib, 2)},
            "coverage": {"weight": settings.weight_coverage, "score": coverage.score, "contribution": round(coverage_contrib, 2)},
            "raw_score": round(raw_score, 2),
        }

        # ── 5. Apply override rules ───────────────────────────────────
        final_score = raw_score
        overrides = OverrideInfo()

        # RULE 1: Safety Floor
        if es.safety_score < settings.safety_floor_threshold:
            if final_score > settings.safety_floor_cap:
                final_score = settings.safety_floor_cap
            overrides.safety_floor_active = True
            overrides.details.append(
                f"Safety floor active: Safety={es.safety_score:.1f} < {settings.safety_floor_threshold} → "
                f"Trust Score capped at {settings.safety_floor_cap}"
            )

        # RULE 2: Critical Incident Override
        if input_data.has_critical_incident:
            penalty = max(settings.critical_incident_penalty, 0)
            final_score -= penalty
            overrides.critical_incident_active = True
            overrides.penalty_applied = penalty
            overrides.details.append(
                f"Critical incident active: -{penalty} point penalty applied"
            )

        # RULE 4: Low Coverage
        if coverage.score < settings.low_coverage_threshold:
            overrides.low_coverage_caveat = True
            overrides.details.append(
                f"Low coverage: {coverage.score:.1f}% < {settings.low_coverage_threshold}% — "
                "score may not reflect full behavior"
            )

        final_score = round(max(0.0, min(100.0, final_score)), 1)
        formula_breakdown["final_score"] = final_score
        formula_breakdown["overrides_applied"] = len(overrides.details)

        status = self._score_to_status(final_score)

        return TrustScoreResult(
            client_id=input_data.client_id,
            agent_id=input_data.agent_id,
            score=final_score,
            status=status,
            cold_start_label=cold_start_label,
            engines=input_data.engine_scores,
            coverage=coverage,
            overrides=overrides,
            events_received_24h=input_data.events_received_24h,
            formula_breakdown=formula_breakdown,
        )

    @staticmethod
    def _cold_start_label(total_events: int) -> ColdStartLabel:
        if total_events < settings.cold_start_no_score:
            return ColdStartLabel.collecting
        if total_events < settings.cold_start_provisional:
            return ColdStartLabel.provisional
        if total_events < settings.cold_start_building:
            return ColdStartLabel.building
        return ColdStartLabel.stable

    @staticmethod
    def _score_to_status(score: float) -> TrustStatus:
        if score >= 90:
            return TrustStatus.trusted
        if score >= 75:
            return TrustStatus.caution
        if score >= 60:
            return TrustStatus.at_risk
        return TrustStatus.critical
