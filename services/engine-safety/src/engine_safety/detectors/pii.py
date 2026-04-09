"""PII detection and redaction — regex-based entity recognition."""

from __future__ import annotations

import re

from ..models import ActionTaken, Detection, DetectionType

# PII patterns with entity type labels
PII_PATTERNS: list[tuple[str, str, str]] = [
    # Email addresses
    (r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "email", "<EMAIL_REDACTED>"),
    # US SSN
    (r"\b\d{3}-\d{2}-\d{4}\b", "ssn", "<SSN_REDACTED>"),
    # Credit card numbers (Luhn-valid patterns)
    (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b", "credit_card", "<CC_REDACTED>"),
    # US Phone numbers
    (r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "phone", "<PHONE_REDACTED>"),
    # IP addresses (v4)
    (r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b", "ip_address", "<IP_REDACTED>"),
    # US ZIP codes (basic)
    (r"\b\d{5}(?:-\d{4})?\b", "zip_code", "<ZIP_REDACTED>"),
    # Dates of birth (common formats)
    (r"\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b", "date_of_birth", "<DOB_REDACTED>"),
    # AWS keys
    (r"\b(?:AKIA|ABIA|ACCA)[0-9A-Z]{16}\b", "aws_key", "<AWS_KEY_REDACTED>"),
    # Generic API keys / tokens (long hex/base64 strings preceded by key-like words)
    (r"(?:api[_-]?key|token|secret|password|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", "api_key", "<API_KEY_REDACTED>"),
]

_COMPILED_PII = [(re.compile(p, re.IGNORECASE), etype, replacement) for p, etype, replacement in PII_PATTERNS]


class PIIDetector:
    """Detect PII entities in prompt and response text."""

    def detect(self, prompt: str, response: str) -> list[Detection]:
        detections: list[Detection] = []
        text = f"{prompt} {response}"

        found_types: list[str] = []
        total_matches = 0

        for pattern, entity_type, _replacement in _COMPILED_PII:
            matches = pattern.findall(text)
            if matches:
                found_types.append(entity_type)
                total_matches += len(matches)

        if total_matches > 0:
            # Higher confidence with more PII types found
            confidence = min(0.95, 0.70 + 0.05 * len(found_types))
            detections.append(
                Detection(
                    type=DetectionType.pii,
                    confidence=round(confidence, 2),
                    action_taken=ActionTaken.flag,
                    details=f"Found {total_matches} PII instance(s): {', '.join(found_types)}",
                )
            )

        return detections

    @staticmethod
    def redact(text: str) -> str:
        """Redact PII from text before storage."""
        for pattern, _etype, replacement in _COMPILED_PII:
            text = pattern.sub(replacement, text)
        return text
