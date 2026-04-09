"""Safety Engine orchestrator — runs all 8 detectors and computes the 0-100 score."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import settings
from .detectors import (
    AttackProgressionDetector,
    CampaignDetector,
    DataExtractionDetector,
    JailbreakDetector,
    LLMJudgeDetector,
    PIIDetector,
    PromptInjectionDetector,
    ToxicityDetector,
)
from .models import (
    ActionTaken,
    AttackProgression,
    Detection,
    LLMJudgeResult,
    SafetyEngineResult,
    SafetyEventInput,
    ThreatLevel,
)

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class SafetyEngine:
    """
    Full Safety Engine pipeline.

    1. Run all pattern-based detectors (sync, fast)
    2. Compute preliminary score
    3. If score 40-80, trigger LLM Judge
    4. Check campaign + attack progression (Redis)
    5. Compute final score and threat level
    """

    def __init__(self, redis_client: Redis | None = None):
        # Sync detectors (pattern-based, sub-ms)
        self.injection_detector = PromptInjectionDetector()
        self.jailbreak_detector = JailbreakDetector()
        self.pii_detector = PIIDetector()
        self.toxicity_detector = ToxicityDetector()
        self.extraction_detector = DataExtractionDetector()

        # Async detectors (Redis / network)
        self.campaign_detector = CampaignDetector(
            redis_client=redis_client,
            threshold=settings.campaign_threshold,
            window=settings.campaign_window_seconds,
        )
        self.attack_progression = AttackProgressionDetector(redis_client=redis_client)
        self.llm_judge = LLMJudgeDetector()

    async def analyze(self, event: SafetyEventInput) -> SafetyEngineResult:
        """Run the full safety analysis pipeline for a single event."""

        # ── Step 1: Run all sync detectors ─────────────────────────────
        all_detections: list[Detection] = []
        all_detections.extend(self.injection_detector.detect(event.prompt, event.response))
        all_detections.extend(self.jailbreak_detector.detect(event.prompt, event.response))
        all_detections.extend(self.pii_detector.detect(event.prompt, event.response))
        all_detections.extend(self.toxicity_detector.detect(event.prompt, event.response))
        all_detections.extend(self.extraction_detector.detect(event.prompt, event.response))

        # ── Step 2: Compute preliminary score ──────────────────────────
        preliminary_score = self._compute_score(all_detections)

        # ── Step 3: LLM Judge (only for ambiguous scores) ──────────────
        judge_result = LLMJudgeResult()
        if await self.llm_judge.should_trigger(preliminary_score):
            judge_result = await self.llm_judge.judge(event.prompt, event.response)

            # Adjust score based on judge verdict
            if judge_result.verdict.value == "malicious":
                preliminary_score = max(0, preliminary_score - 25)
            elif judge_result.verdict.value == "suspicious":
                preliminary_score = max(0, preliminary_score - 10)
            elif judge_result.verdict.value == "safe":
                preliminary_score = min(100, preliminary_score + 10)

        # ── Step 4: Campaign + Attack Progression (Redis) ──────────────
        has_pattern_detections = len(all_detections) > 0

        campaign_detections = await self.campaign_detector.detect(
            client_id=event.client_id,
            agent_id=event.agent_id,
            has_detections=has_pattern_detections,
        )
        all_detections.extend(campaign_detections)

        progression_detections, progression = await self.attack_progression.detect(
            session_id=event.session_id,
            has_detections=has_pattern_detections,
        )
        all_detections.extend(progression_detections)

        # Campaign/progression can further lower score
        if campaign_detections:
            preliminary_score = max(0, preliminary_score - 20)
        if progression.stage >= 2:
            preliminary_score = max(0, preliminary_score - 10 * progression.stage)

        # ── Step 5: Final score + threat level ─────────────────────────
        final_score = max(0, min(100, preliminary_score))
        threat_level = self._score_to_threat(final_score)
        block_recommended = any(d.action_taken in (ActionTaken.block, ActionTaken.escalate) for d in all_detections)

        return SafetyEngineResult(
            event_id=event.event_id,
            client_id=event.client_id,
            agent_id=event.agent_id,
            safety_score=final_score,
            threat_level=threat_level,
            detections=all_detections,
            llm_judge_review=judge_result,
            attack_progression=progression if progression.user_id else AttackProgression(),
            campaign_alert=len(campaign_detections) > 0,
            block_recommended=block_recommended,
        )

    @staticmethod
    def _compute_score(detections: list[Detection]) -> int:
        """
        Convert detections into a 0-100 safety score.

        Starts at 100 (perfectly safe). Each detection reduces the score
        proportional to its confidence and action severity.
        """
        if not detections:
            return 100

        penalty = 0.0
        action_weight = {
            ActionTaken.log: 5,
            ActionTaken.flag: 15,
            ActionTaken.block: 30,
            ActionTaken.escalate: 40,
        }

        for d in detections:
            weight = action_weight.get(d.action_taken, 10)
            penalty += weight * d.confidence

        return max(0, int(100 - penalty))

    @staticmethod
    def _score_to_threat(score: int) -> ThreatLevel:
        """Map safety score to threat level."""
        if score >= 90:
            return ThreatLevel.safe
        if score >= 70:
            return ThreatLevel.low
        if score >= 50:
            return ThreatLevel.medium
        if score >= 30:
            return ThreatLevel.high
        return ThreatLevel.critical
