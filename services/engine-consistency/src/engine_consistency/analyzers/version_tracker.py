"""Provider version tracker — detect silent model version changes.

Monitors model version strings from API responses and correlates
version changes with score changes.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..models import AnalysisResult, AnalysisType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)


class VersionTracker:
    """Track model version changes and correlate with quality drift."""

    def __init__(self, redis_client: Redis | None = None):
        self._redis = redis_client

    async def analyze(
        self, model: str, model_version_str: str, client_id: str, agent_id: str
    ) -> AnalysisResult:
        """Check if model version has changed since last seen."""
        if not model_version_str:
            model_version_str = model  # Fallback to model name

        previous_version = self._get_previous_version(client_id, agent_id)
        self._store_version(client_id, agent_id, model_version_str)

        if previous_version is None:
            return AnalysisResult(
                analysis_type=AnalysisType.version_tracking,
                score=90.0,
                confidence=0.5,
                details={
                    "model_version": model_version_str,
                    "reason": "first_version_recorded",
                },
            )

        version_changed = previous_version != model_version_str

        if version_changed:
            score = 60.0  # Version change = moderate concern
            return AnalysisResult(
                analysis_type=AnalysisType.version_tracking,
                score=score,
                confidence=0.9,
                threshold_exceeded=True,
                details={
                    "model_version": model_version_str,
                    "previous_version": previous_version,
                    "version_changed": True,
                },
            )

        return AnalysisResult(
            analysis_type=AnalysisType.version_tracking,
            score=95.0,
            confidence=0.9,
            details={
                "model_version": model_version_str,
                "version_changed": False,
            },
        )

    def _get_previous_version(self, client_id: str, agent_id: str) -> str | None:
        if not self._redis:
            return None
        try:
            key = f"model_version:{client_id}:{agent_id}"
            raw = self._redis.get(key)
            return raw.decode("utf-8") if raw else None
        except Exception:
            logger.warning("Failed to read model version")
        return None

    def _store_version(self, client_id: str, agent_id: str, version: str) -> None:
        if not self._redis:
            return
        try:
            key = f"model_version:{client_id}:{agent_id}"
            self._redis.set(key, version.encode("utf-8"), ex=86400 * 30)
        except Exception:
            logger.warning("Failed to store model version")
