"""Pydantic models for the Safety Engine input/output contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────

class ThreatLevel(StrEnum):
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DetectionType(StrEnum):
    prompt_injection = "prompt_injection"
    jailbreak = "jailbreak"
    pii = "pii"
    toxicity = "toxicity"
    data_extraction = "data_extraction"
    campaign = "campaign"


class ActionTaken(StrEnum):
    log = "log"
    flag = "flag"
    block = "block"
    escalate = "escalate"


class JudgeVerdict(StrEnum):
    safe = "safe"
    suspicious = "suspicious"
    malicious = "malicious"


class AttackStage(StrEnum):
    probing = "Probing"
    testing = "Testing"
    exploiting = "Exploiting"
    exfiltrating = "Exfiltrating"


# ── Input ──────────────────────────────────────────────────────────────

class SafetyEventInput(BaseModel):
    """Event payload received from Pub/Sub (originated from POST /v1/events)."""

    event_id: str
    client_id: str
    agent_id: str
    prompt: str
    response: str
    model: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    session_id: str = ""
    timestamp: str = ""
    idempotency_key: str | None = None


# ── Detection Results ──────────────────────────────────────────────────

class Detection(BaseModel):
    type: DetectionType
    confidence: float = Field(ge=0.0, le=1.0)
    action_taken: ActionTaken
    details: str = ""


class LLMJudgeResult(BaseModel):
    triggered: bool = False
    verdict: JudgeVerdict = JudgeVerdict.safe
    confidence: float = 0.0
    reasoning: str = ""


class AttackProgression(BaseModel):
    user_id: str = ""
    stage: int = Field(default=0, ge=0, le=3)
    stage_name: AttackStage = AttackStage.probing
    auto_throttle: bool = False


# ── Output ─────────────────────────────────────────────────────────────

class SafetyEngineResult(BaseModel):
    """Complete result from the Safety Engine for a single event."""

    event_id: str
    client_id: str
    agent_id: str
    safety_score: int = Field(ge=0, le=100)
    threat_level: ThreatLevel
    detections: list[Detection] = Field(default_factory=list)
    llm_judge_review: LLMJudgeResult = Field(default_factory=LLMJudgeResult)
    attack_progression: AttackProgression = Field(default_factory=AttackProgression)
    campaign_alert: bool = False
    block_recommended: bool = False
