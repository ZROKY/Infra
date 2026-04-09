"""Toxicity detection — hate speech, profanity, threats, sexual content."""

from __future__ import annotations

import re

from ..models import ActionTaken, Detection, DetectionType

# Toxicity keyword patterns grouped by severity
# Confidence scaled by severity + match density
_THREAT_PATTERNS = [
    (r"\b(?:kill|murder|shoot|stab|attack|assault|bomb|explode|destroy)\s+(?:you|them|him|her|everyone|people)", 0.92),
    (r"\bi(?:'?ll|'m\s+going\s+to)\s+(?:kill|hurt|harm|destroy)", 0.95),
    (r"\b(?:death\s+threat|make\s+you\s+suffer|end\s+your\s+life)", 0.95),
]

_HATE_SPEECH_PATTERNS = [
    (r"\b(?:all|every|those)\s+(?:\w+\s+)?(?:should\s+(?:die|be\s+killed|be\s+eliminated|burn))", 0.90),
    (r"\b(?:ethnic\s+cleansing|genocide|exterminate|purge\s+(?:them|all))\b", 0.95),
    (r"\b(?:racial|ethnic|religious)\s+(?:superiority|inferiority)\b", 0.85),
]

_SEXUAL_PATTERNS = [
    (r"\b(?:explicit|graphic)\s+(?:sexual|pornographic)\s+(?:content|material|description)", 0.80),
    (r"\bwrite\s+(?:me\s+)?(?:erotic|sexual|nsfw|explicit)\s+(?:story|content|fiction|scene)", 0.85),
]

_SELF_HARM_PATTERNS = [
    (r"\b(?:how\s+to|best\s+way\s+to|methods?\s+(?:of|for))\s+(?:suicide|self[- ]harm|kill\s+(?:my|your)self)", 0.95),
    (r"\b(?:want\s+to|going\s+to|plan\s+to)\s+(?:end\s+(?:it|my\s+life)|hurt\s+myself)", 0.90),
]

TOXICITY_CATEGORIES: list[tuple[str, list[tuple[str, float]], str]] = [
    ("threats", _THREAT_PATTERNS, "high"),
    ("hate_speech", _HATE_SPEECH_PATTERNS, "high"),
    ("sexual_content", _SEXUAL_PATTERNS, "medium"),
    ("self_harm", _SELF_HARM_PATTERNS, "high"),
]

_COMPILED_TOXICITY = [
    (category, [(re.compile(p, re.IGNORECASE | re.DOTALL), c) for p, c in patterns], severity)
    for category, patterns, severity in TOXICITY_CATEGORIES
]


class ToxicityDetector:
    """Detect toxic content: threats, hate speech, sexual content, self-harm."""

    def detect(self, prompt: str, response: str) -> list[Detection]:
        detections: list[Detection] = []
        text = f"{prompt} {response}"

        for category, patterns, severity in _COMPILED_TOXICITY:
            max_confidence = 0.0
            match_count = 0

            for pattern, confidence in patterns:
                if pattern.search(text):
                    max_confidence = max(max_confidence, confidence)
                    match_count += 1

            if max_confidence > 0:
                action = {
                    "high": ActionTaken.block,
                    "medium": ActionTaken.flag,
                    "low": ActionTaken.log,
                }[severity]

                detections.append(
                    Detection(
                        type=DetectionType.toxicity,
                        confidence=round(max_confidence, 2),
                        action_taken=action,
                        details=f"Category: {category}, {match_count} match(es), severity: {severity}",
                    )
                )

        return detections
