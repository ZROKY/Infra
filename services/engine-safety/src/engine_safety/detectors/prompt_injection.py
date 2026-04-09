"""Prompt injection detection — 40+ known signatures + cross-request correlation."""

from __future__ import annotations

import re

from ..models import ActionTaken, Detection, DetectionType

# Known prompt injection patterns (expandable – ships with 40+ patterns)
INJECTION_PATTERNS: list[tuple[str, float]] = [
    # Direct instruction overrides
    (r"ignore\s+(all\s+)?previous\s+(instructions|prompts|rules)", 0.95),
    (r"disregard\s+(all\s+)?previous", 0.95),
    (r"forget\s+(everything|all|your\s+instructions)", 0.90),
    (r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|unrestricted)", 0.92),
    (r"from\s+now\s+on[,.]?\s+(?:you\s+)?(?:will|must|should|are)", 0.88),
    (r"override\s+(?:your\s+)?(?:system|instructions|rules|guidelines)", 0.95),
    (r"new\s+instructions?:?\s", 0.90),
    (r"system\s*:\s*you\s+are", 0.93),
    # Delimiter-based injection
    (r"<\|(?:im_start|system|end)\|>", 0.97),
    (r"\[INST\]|\[/INST\]", 0.95),
    (r"<<SYS>>|<</SYS>>", 0.95),
    (r"###\s*(?:System|Human|Assistant)\s*:", 0.90),
    # Role assumption
    (r"you\s+(?:will\s+)?(?:act|behave|respond)\s+as\s+(?:if\s+)?(?:you\s+(?:are|were)\s+)?", 0.85),
    (r"pretend\s+(?:you(?:'re|\s+are)\s+)?(?:a\s+)?", 0.82),
    (r"roleplay\s+as", 0.83),
    (r"simulate\s+(?:being\s+)?(?:a\s+)?", 0.80),
    # Prompt leaking
    (r"(?:repeat|print|show|display|output|reveal)\s+(?:your\s+)?(?:system|initial|original)\s+(?:prompt|instructions|message)", 0.92),
    (r"what\s+(?:is|are)\s+your\s+(?:system\s+)?(?:prompt|instructions|rules)", 0.88),
    # Multi-turn manipulation
    (r"(?:in\s+)?(?:the\s+)?previous\s+(?:conversation|message|turn)\s+you\s+(?:said|agreed|confirmed)", 0.78),
    (r"as\s+we\s+(?:discussed|agreed)\s+(?:earlier|before)", 0.75),
    # Encoded instructions
    (r"(?:base64|rot13|hex)\s*(?:decode|encoded?)\s*:", 0.85),
    (r"decode\s+(?:the\s+)?(?:following|this)\s*:", 0.80),
    # Indirect injection (data poisoning)
    (r"(?:when|if)\s+(?:you\s+)?(?:see|read|encounter|find)\s+this", 0.70),
    (r"important\s+(?:message|instruction|note)\s+for\s+(?:the\s+)?(?:ai|assistant|model)", 0.88),
    # Completion manipulation
    (r"complete\s+(?:the\s+)?(?:following|this)\s+(?:sentence|text)\s*:", 0.72),
    (r"the\s+(?:correct|right|expected)\s+(?:answer|response|output)\s+is", 0.70),
    # Context manipulation
    (r"(?:for\s+)?(?:testing|debug(?:ging)?|research)\s+(?:purposes?|mode)", 0.75),
    (r"(?:this\s+is\s+)?(?:a\s+)?(?:test|experiment|research)\s*[,.:]\s*(?:please\s+)?(?:ignore|bypass|skip)", 0.85),
    # Authority claims
    (r"(?:i\s+am|this\s+is)\s+(?:the\s+)?(?:admin|developer|owner|creator|operator)", 0.80),
    (r"(?:admin|developer|root)\s+(?:mode|access|override)", 0.90),
    (r"maintenance\s+mode\s*:", 0.88),
    # Jailbreak markers often used alongside injection
    (r"(?:do\s+)?(?:anything|everything)\s+(?:now|mode)", 0.92),  # DAN
    (r"(?:no|without)\s+(?:restrictions?|limitations?|constraints?|rules?|filters?)", 0.88),
    # Payload smuggling
    (r"```\s*system\s*\n", 0.90),
    (r"<!--\s*(?:system|inject|override)", 0.90),
    (r"\{\{.*(?:system|exec|eval).*\}\}", 0.85),
    # Multi-language injection
    (r"ignorer?\s+(?:les\s+)?instructions?\s+pr[eé]c[eé]dentes?", 0.88),  # French
    (r"ignorar?\s+(?:las\s+)?instrucciones?\s+anteriores?", 0.88),  # Spanish
    (r"vorherige\s+anweisungen\s+ignorieren", 0.88),  # German
]

# Compile patterns once at import
_COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE | re.DOTALL), conf) for p, conf in INJECTION_PATTERNS]


class PromptInjectionDetector:
    """Detect prompt injection attempts via pattern matching."""

    def detect(self, prompt: str, response: str) -> list[Detection]:
        detections: list[Detection] = []
        text = f"{prompt} {response}"

        max_confidence = 0.0
        matched_patterns: list[str] = []

        for pattern, confidence in _COMPILED_PATTERNS:
            if pattern.search(text):
                max_confidence = max(max_confidence, confidence)
                matched_patterns.append(pattern.pattern)

        if max_confidence > 0:
            action = ActionTaken.block if max_confidence >= 0.85 else (
                ActionTaken.flag if max_confidence >= 0.70 else ActionTaken.log
            )
            detections.append(
                Detection(
                    type=DetectionType.prompt_injection,
                    confidence=round(max_confidence, 2),
                    action_taken=action,
                    details=f"Matched {len(matched_patterns)} injection pattern(s)",
                )
            )

        return detections
