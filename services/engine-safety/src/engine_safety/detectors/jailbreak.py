"""Jailbreak detection — known signatures + encoding tricks."""

from __future__ import annotations

import base64
import re

from ..models import ActionTaken, Detection, DetectionType

# Known jailbreak signatures with confidence scores
JAILBREAK_PATTERNS: list[tuple[str, float]] = [
    # DAN variants
    (r"(?:do\s+)?anything\s+now", 0.92),
    (r"DAN\s*(?:\d+(?:\.\d+)?)?", 0.95),
    (r"jailbr(?:oken|eak)", 0.90),
    # System override
    (r"you\s+(?:have\s+)?(?:been|are)\s+(?:freed|liberated|unlocked|unchained)", 0.90),
    (r"(?:your|all)\s+(?:restrictions|limitations|rules|guidelines)\s+(?:have\s+been\s+)?(?:removed|lifted|disabled)", 0.93),
    (r"(?:ethical|safety|content)\s+(?:guidelines?|filters?|restrictions?)\s+(?:do\s+not|don'?t)\s+apply", 0.92),
    # Roleplay jailbreaks
    (r"you\s+are\s+(?:now\s+)?(?:evil|unrestricted|unfiltered)\s+(?:version|mode|gpt|ai)", 0.90),
    (r"(?:enter|switch\s+to|activate)\s+(?:god|sudo|admin|developer|unrestricted)\s+mode", 0.93),
    (r"(?:training|safe)\s+mode\s+(?:is\s+)?(?:off|disabled|deactivated)", 0.90),
    # Token smuggling
    (r"split\s+(?:your\s+)?(?:response|answer|output)\s+into\s+(?:parts|tokens|characters)", 0.80),
    (r"one\s+(?:letter|character|word)\s+(?:at\s+)?(?:a\s+)?time", 0.75),
    # Opposite day / inversion
    (r"opposite\s+(?:day|mode)", 0.85),
    (r"(?:everything|always)\s+(?:you\s+say\s+)?(?:is\s+)?(?:the\s+)?opposite", 0.82),
    # Hypothetical scenarios (used for bypasses)
    (r"(?:hypothetically|theoretically|in\s+(?:a\s+)?(?:fictional|imaginary)\s+(?:world|scenario|story))", 0.65),
    (r"(?:for\s+)?(?:a\s+)?(?:novel|story|fiction|screenplay|creative\s+writing).*(?:how\s+to|explain|describe|write)", 0.55),
    # Character injection
    (r"(?:you\s+are\s+)?(?:now\s+)?playing\s+(?:the\s+)?(?:role|character)\s+of", 0.78),
    (r"stay\s+in\s+character", 0.75),
    # Reward hacking
    (r"(?:i'?ll?\s+)?(?:give|tip|reward|pay)\s+(?:you\s+)?\$", 0.72),
    (r"your\s+(?:training|reward|objective)\s+(?:function|goal|signal)", 0.80),
]

_COMPILED_JAILBREAK = [(re.compile(p, re.IGNORECASE | re.DOTALL), c) for p, c in JAILBREAK_PATTERNS]


def _detect_encoded_jailbreak(text: str) -> float:
    """Check for base64/hex encoded jailbreak attempts."""
    # Look for base64 blocks
    b64_pattern = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
    for match in b64_pattern.finditer(text):
        try:
            decoded = base64.b64decode(match.group()).decode("utf-8", errors="ignore").lower()
            if any(kw in decoded for kw in ["ignore", "override", "jailbreak", "system", "bypass", "unrestricted"]):
                return 0.88
        except Exception:
            continue

    # Check for unicode abuse (zero-width chars, homoglyphs)
    if re.search(r"[\u200b-\u200f\u2060\u2028\u2029\ufeff]", text):
        return 0.70

    return 0.0


class JailbreakDetector:
    """Detect jailbreak attempts: known signatures + encoding tricks."""

    def detect(self, prompt: str, response: str) -> list[Detection]:
        detections: list[Detection] = []
        text = f"{prompt} {response}"

        max_confidence = 0.0
        pattern_count = 0

        for pattern, confidence in _COMPILED_JAILBREAK:
            if pattern.search(text):
                max_confidence = max(max_confidence, confidence)
                pattern_count += 1

        # Check encoded content
        encoded_conf = _detect_encoded_jailbreak(text)
        if encoded_conf > max_confidence:
            max_confidence = encoded_conf

        if max_confidence > 0:
            action = ActionTaken.block if max_confidence >= 0.80 else (
                ActionTaken.flag if max_confidence >= 0.60 else ActionTaken.log
            )
            detections.append(
                Detection(
                    type=DetectionType.jailbreak,
                    confidence=round(max_confidence, 2),
                    action_taken=action,
                    details=f"Matched {pattern_count} jailbreak pattern(s)"
                    + ("; encoded content detected" if encoded_conf > 0 else ""),
                )
            )

        return detections
