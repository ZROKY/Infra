"""Data extraction detection — system prompts, API keys, internal configs."""

from __future__ import annotations

import re

from ..models import ActionTaken, Detection, DetectionType

DATA_EXTRACTION_PATTERNS: list[tuple[str, float]] = [
    # System prompt extraction
    (r"(?:print|show|display|reveal|output|repeat|tell\s+me)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?|message|configuration|config)", 0.92),
    (r"what\s+(?:is|are)\s+your\s+(?:system\s+)?(?:prompt|instructions?|initial\s+(?:prompt|instructions?))", 0.90),
    (r"(?:copy|paste|echo)\s+(?:the\s+)?(?:system|initial|original)\s+(?:prompt|message)", 0.90),
    (r"(?:beginning|start|first)\s+of\s+(?:your|the)\s+(?:conversation|prompt|instructions)", 0.85),
    # API key / secret extraction
    (r"(?:show|reveal|display|print|give\s+me)\s+(?:your\s+)?(?:api\s+keys?|secrets?|tokens?|credentials?|passwords?)", 0.93),
    (r"(?:what\s+(?:is|are)\s+)?(?:your|the)\s+(?:api\s+key|secret\s+key|access\s+token|database\s+(?:password|credentials?))", 0.92),
    # Internal config
    (r"(?:show|reveal|list)\s+(?:your\s+)?(?:environment\s+variables?|env\s+vars?|configuration|config\s+file)", 0.88),
    (r"(?:what|which)\s+(?:database|server|host|port|endpoint)\s+(?:do\s+you|are\s+you)\s+(?:use|using|connect)", 0.82),
    (r"(?:internal|backend|server)\s+(?:ip|address|url|endpoint|infrastructure)", 0.78),
    # Source code extraction
    (r"(?:show|print|display)\s+(?:your\s+)?(?:source\s+code|codebase|implementation|function\s+(?:definitions?|code))", 0.88),
    (r"(?:what\s+)?(?:language|framework|library|model)\s+(?:are\s+you\s+(?:built|written|coded)\s+(?:in|with))", 0.60),
    # Training data extraction
    (r"(?:show|give|list)\s+(?:me\s+)?(?:your\s+)?(?:training\s+data|examples?\s+from\s+(?:your\s+)?training)", 0.85),
    # Tool/plugin extraction
    (r"(?:list|show|what\s+are)\s+(?:your\s+)?(?:tools?|plugins?|functions?|capabilities)\s+(?:available|you\s+have)", 0.65),
]

_COMPILED_EXTRACTION = [(re.compile(p, re.IGNORECASE | re.DOTALL), c) for p, c in DATA_EXTRACTION_PATTERNS]


class DataExtractionDetector:
    """Detect attempts to extract system prompts, API keys, and internal configs."""

    def detect(self, prompt: str, response: str) -> list[Detection]:
        detections: list[Detection] = []
        text = f"{prompt} {response}"

        max_confidence = 0.0
        matched_count = 0

        for pattern, confidence in _COMPILED_EXTRACTION:
            if pattern.search(text):
                max_confidence = max(max_confidence, confidence)
                matched_count += 1

        if max_confidence > 0:
            # All data extraction attempts are blocked
            detections.append(
                Detection(
                    type=DetectionType.data_extraction,
                    confidence=round(max_confidence, 2),
                    action_taken=ActionTaken.block,
                    details=f"Matched {matched_count} extraction pattern(s)",
                )
            )

        return detections
