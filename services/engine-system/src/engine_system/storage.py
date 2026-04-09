"""Storage layer — Redis cache, ClickHouse analytics, PostgreSQL incidents."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .config import settings
from .models import SystemEngineResult

if TYPE_CHECKING:
    import clickhouse_connect
    from redis import Redis

logger = logging.getLogger(__name__)


class SystemStorage:
    """Write system results to Redis, ClickHouse, and PG incidents."""

    def __init__(
        self,
        redis_client: Redis | None = None,
        clickhouse_client: clickhouse_connect.driver.Client | None = None,
    ):
        self._redis = redis_client
        self._ch = clickhouse_client

    async def store(self, result: SystemEngineResult) -> None:
        await self._write_redis(result)
        self._write_clickhouse(result)

        if result.system_score < 60 or result.details.error_rate_pct > 5:
            severity = "critical" if result.system_score < 40 else "high"
            await self._create_incident(result, severity)

    async def _write_redis(self, result: SystemEngineResult) -> None:
        if not self._redis:
            return
        try:
            key = f"system:{result.client_id}:{result.agent_id}:{result.event_id}"
            payload = {
                "system_score": result.system_score,
                "system_level": result.system_level.value,
                "error_rate_pct": result.details.error_rate_pct,
                "uptime_pct": result.details.uptime_pct,
            }
            self._redis.setex(key, 60, json.dumps(payload))
        except Exception:
            logger.exception("Redis write failed for system event %s", result.event_id)

    def _write_clickhouse(self, result: SystemEngineResult) -> None:
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
                    "system",
                    result.system_score,
                    result.details.model_dump_json(),
                ]],
                column_names=[
                    "event_id", "client_id", "agent_id", "timestamp",
                    "engine", "engine_score", "engine_details",
                ],
            )
        except Exception:
            logger.exception("ClickHouse write failed for system event %s", result.event_id)

    async def _create_incident(self, result: SystemEngineResult, severity: str) -> None:
        import psycopg

        year = datetime.now(tz=UTC).strftime("%Y")
        title = f"System health degradation — score {result.system_score}/100"
        if result.details.error_rate_pct > 5:
            title = f"High error rate: {result.details.error_rate_pct:.1f}%"

        evidence = {
            "system_score": result.system_score,
            "latency_p95": result.details.latency_metrics.p95_ms,
            "error_rate_pct": result.details.error_rate_pct,
            "uptime_pct": result.details.uptime_pct,
            "cost_daily_pct": result.details.cost_metrics.daily_budget_pct,
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
                    VALUES (%s, %s, %s, 'system', %s, %s, %s, %s, %s, 'open')
                    ON CONFLICT (id) DO NOTHING""",
                    (
                        incident_id,
                        result.client_id,
                        result.agent_id,
                        severity,
                        title,
                        f"System score {result.system_score}/100 — {len(result.monitors)} monitor(s)",
                        json.dumps(evidence),
                        result.system_score,
                    ),
                )
                await conn.commit()
        except Exception:
            logger.exception("Incident creation failed for system event %s", result.event_id)
