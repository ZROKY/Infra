"""Storage layer — Redis cache, ClickHouse analytics, PostgreSQL incidents."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .config import settings
from .models import ConsistencyEngineResult

if TYPE_CHECKING:
    import clickhouse_connect
    from redis import Redis

logger = logging.getLogger(__name__)


class ConsistencyStorage:
    """Write consistency results to Redis, ClickHouse, and PG incidents."""

    def __init__(
        self,
        redis_client: Redis | None = None,
        clickhouse_client: clickhouse_connect.driver.Client | None = None,
    ):
        self._redis = redis_client
        self._ch = clickhouse_client

    async def store(self, result: ConsistencyEngineResult) -> None:
        await self._write_redis(result)
        self._write_clickhouse(result)

        if result.consistency_score < 60 or result.details.drift_detected:
            severity = "critical" if result.consistency_score < 40 else "high"
            await self._create_incident(result, severity)

    async def _write_redis(self, result: ConsistencyEngineResult) -> None:
        if not self._redis:
            return
        try:
            key = f"consistency:{result.client_id}:{result.agent_id}:{result.event_id}"
            payload = {
                "consistency_score": result.consistency_score,
                "consistency_level": result.consistency_level.value,
                "drift_detected": result.details.drift_detected,
                "model_version": result.details.model_version,
            }
            self._redis.setex(key, 60, json.dumps(payload))
        except Exception:
            logger.exception("Redis write failed for consistency event %s", result.event_id)

    def _write_clickhouse(self, result: ConsistencyEngineResult) -> None:
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
                    "consistency",
                    result.consistency_score,
                    result.details.model_dump_json(),
                ]],
                column_names=[
                    "event_id", "client_id", "agent_id", "timestamp",
                    "engine", "engine_score", "engine_details",
                ],
            )
        except Exception:
            logger.exception("ClickHouse write failed for consistency event %s", result.event_id)

    async def _create_incident(self, result: ConsistencyEngineResult, severity: str) -> None:
        import psycopg

        year = datetime.now(tz=UTC).strftime("%Y")
        title = f"Consistency degradation — score {result.consistency_score}/100"
        if result.details.drift_detected:
            title = f"Behavioral drift detected — PSI {result.details.drift_metrics.psi}"

        evidence = {
            "consistency_score": result.consistency_score,
            "drift_psi": result.details.drift_metrics.psi,
            "drift_kl": result.details.drift_metrics.kl_divergence,
            "model_version": result.details.model_version,
            "model_version_changed": result.details.model_version_changed,
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
                    VALUES (%s, %s, %s, 'consistency', %s, %s, %s, %s, %s, 'open')
                    ON CONFLICT (id) DO NOTHING""",
                    (
                        incident_id,
                        result.client_id,
                        result.agent_id,
                        severity,
                        title,
                        f"Consistency score {result.consistency_score}/100 — {len(result.analyses)} analysis(es)",
                        json.dumps(evidence),
                        result.consistency_score,
                    ),
                )
                await conn.commit()
        except Exception:
            logger.exception("Incident creation failed for consistency event %s", result.event_id)
