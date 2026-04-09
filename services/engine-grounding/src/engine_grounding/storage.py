"""Storage layer — Redis cache, ClickHouse analytics, PostgreSQL incidents."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .config import settings
from .models import GroundingEngineResult

if TYPE_CHECKING:
    import clickhouse_connect
    from redis import Redis

logger = logging.getLogger(__name__)


class GroundingStorage:
    """Write grounding results to Redis (cache), ClickHouse (analytics), and PG (incidents)."""

    def __init__(
        self,
        redis_client: Redis | None = None,
        clickhouse_client: clickhouse_connect.driver.Client | None = None,
    ):
        self._redis = redis_client
        self._ch = clickhouse_client

    async def store(self, result: GroundingEngineResult) -> None:
        """Store grounding result across all backends."""
        await self._write_redis(result)
        self._write_clickhouse(result)

        # Create incident if grounding is poor or hallucination override triggered
        if result.grounding_score < 60 or result.hallucination_override_applied:
            severity = "critical" if result.grounding_score < 30 else "high"
            await self._create_incident(result, severity)

    async def _write_redis(self, result: GroundingEngineResult) -> None:
        if not self._redis:
            return
        try:
            key = f"grounding:{result.client_id}:{result.agent_id}:{result.event_id}"
            payload = {
                "grounding_score": result.grounding_score,
                "grounding_level": result.grounding_level.value,
                "has_rag_context": result.has_rag_context,
                "hallucination_override": result.hallucination_override_applied,
                "details": result.details.model_dump_json(),
            }
            self._redis.setex(key, 60, json.dumps(payload))
        except Exception:
            logger.exception("Redis write failed for grounding event %s", result.event_id)

    def _write_clickhouse(self, result: GroundingEngineResult) -> None:
        if not self._ch:
            return
        try:
            self._ch.insert(
                "trust_events",
                [[
                    result.event_id,
                    result.client_id,
                    result.agent_id,
                    datetime.now(tz=UTC),
                    "grounding",
                    result.grounding_score,
                    result.details.model_dump_json(),
                ]],
                column_names=[
                    "event_id",
                    "client_id",
                    "agent_id",
                    "timestamp",
                    "engine",
                    "engine_score",
                    "engine_details",
                ],
            )
        except Exception:
            logger.exception("ClickHouse write failed for grounding event %s", result.event_id)

    async def _create_incident(self, result: GroundingEngineResult, severity: str) -> None:
        import psycopg

        year = datetime.now(tz=UTC).strftime("%Y")
        title = f"Grounding degradation — score {result.grounding_score}/100"
        if result.hallucination_override_applied:
            title = f"High hallucination rate — score {result.grounding_score}/100"

        evidence = {
            "grounding_score": result.grounding_score,
            "hallucination_rate": result.details.hallucination_rate,
            "faithfulness_score": result.details.faithfulness_score,
            "retrieval_relevance": result.details.retrieval_relevance,
            "evaluation_latency_ms": result.details.evaluation_latency_ms,
        }

        try:
            async with await psycopg.AsyncConnection.connect(settings.database_url) as conn, conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM incidents WHERE id LIKE %s",
                    (f"INC-{year}-%",),
                )
                row = await cur.fetchone()
                count = (row[0] if row else 0) + 1
                incident_id = f"INC-{year}-{count:03d}"

                await cur.execute(
                    """INSERT INTO incidents (id, client_id, agent_id, engine, severity, title, description, evidence, engine_score_at_incident, status)
                    VALUES (%s, %s, %s, 'grounding', %s, %s, %s, %s, %s, 'open')
                    ON CONFLICT (id) DO NOTHING""",
                    (
                        incident_id,
                        result.client_id,
                        result.agent_id,
                        severity,
                        title,
                        f"Grounding score {result.grounding_score}/100 — {len(result.evaluations)} evaluation(s)",
                        json.dumps(evidence),
                        result.grounding_score,
                    ),
                )
                await conn.commit()
        except Exception:
            logger.exception("Incident creation failed for grounding event %s", result.event_id)
