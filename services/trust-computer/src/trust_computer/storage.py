"""Storage layer — Redis cache, ClickHouse analytics, PostgreSQL incidents."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .config import settings
from .models import TrustScoreResult

if TYPE_CHECKING:
    import clickhouse_connect
    from redis import Redis

logger = logging.getLogger(__name__)


class TrustStorage:
    """Write trust score results to Redis, ClickHouse, and PG incidents."""

    def __init__(
        self,
        redis_client: Redis | None = None,
        clickhouse_client: clickhouse_connect.driver.Client | None = None,
    ):
        self._redis = redis_client
        self._ch = clickhouse_client

    async def store(self, result: TrustScoreResult) -> None:
        self._write_redis(result)
        self._write_clickhouse(result)

        if result.score is not None and result.score < 60:
            severity = "critical" if result.score < 40 else "high"
            await self._create_incident(result, severity)

    def _write_redis(self, result: TrustScoreResult) -> None:
        if not self._redis:
            return
        try:
            # Trust score cache (60s TTL per V1 spec)
            key = f"trust_score:{result.client_id}:{result.agent_id}"
            payload = {
                "score": result.score,
                "status": result.status.value,
                "cold_start_label": result.cold_start_label.value,
                "safety": result.engines.safety_score,
                "grounding": result.engines.grounding_score,
                "consistency": result.engines.consistency_score,
                "system": result.engines.system_score,
                "coverage_score": result.coverage.score,
                "events_received_24h": result.events_received_24h,
            }
            self._redis.setex(key, 60, json.dumps(payload))

            # Engine scores cache (60s TTL)
            engine_key = f"engine_scores:{result.client_id}:{result.agent_id}"
            engine_payload = {
                "safety": result.engines.safety_score,
                "grounding": result.engines.grounding_score,
                "consistency": result.engines.consistency_score,
                "system": result.engines.system_score,
            }
            self._redis.setex(engine_key, 60, json.dumps(engine_payload))
        except Exception:
            logger.exception("Redis write failed for trust score %s:%s", result.client_id, result.agent_id)

    def _write_clickhouse(self, result: TrustScoreResult) -> None:
        if not self._ch:
            return
        try:
            self._ch.insert(
                "trust_events",
                [[
                    "",  # event_id (aggregate, not per-event)
                    result.client_id,
                    result.agent_id,
                    datetime.now(tz=UTC),
                    "trust_computer",
                    result.score or 0.0,
                    json.dumps({
                        "status": result.status.value,
                        "cold_start_label": result.cold_start_label.value,
                        "safety": result.engines.safety_score,
                        "grounding": result.engines.grounding_score,
                        "consistency": result.engines.consistency_score,
                        "system": result.engines.system_score,
                        "coverage": result.coverage.score,
                        "overrides": [d for d in result.overrides.details],
                    }),
                ]],
                column_names=[
                    "event_id", "client_id", "agent_id", "timestamp",
                    "engine", "engine_score", "engine_details",
                ],
            )
        except Exception:
            logger.exception("ClickHouse write failed for trust score %s:%s", result.client_id, result.agent_id)

    async def _create_incident(self, result: TrustScoreResult, severity: str) -> None:
        import psycopg

        year = datetime.now(tz=UTC).strftime("%Y")
        title = f"Trust Score critical — {result.score}/100 ({result.status.value})"

        evidence = {
            "trust_score": result.score,
            "status": result.status.value,
            "safety": result.engines.safety_score,
            "grounding": result.engines.grounding_score,
            "consistency": result.engines.consistency_score,
            "system": result.engines.system_score,
            "coverage": result.coverage.score,
            "overrides": result.overrides.details,
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
                    VALUES (%s, %s, %s, 'trust_computer', %s, %s, %s, %s, %s, 'open')
                    ON CONFLICT (id) DO NOTHING""",
                    (
                        incident_id,
                        result.client_id,
                        result.agent_id,
                        severity,
                        title,
                        f"Trust Score {result.score}/100 — status: {result.status.value}",
                        json.dumps(evidence),
                        result.score,
                    ),
                )
                await conn.commit()
        except Exception:
            logger.exception("Incident creation failed for trust score %s:%s", result.client_id, result.agent_id)
