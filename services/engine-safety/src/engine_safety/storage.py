"""Storage layer — write Safety Engine results to ClickHouse, Redis, and PostgreSQL."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import clickhouse_connect
    from redis import Redis

from .models import SafetyEngineResult, ThreatLevel

logger = logging.getLogger(__name__)


class SafetyStorage:
    """Persist Safety Engine results to all three data stores."""

    def __init__(
        self,
        redis: Redis | None = None,
        clickhouse: clickhouse_connect.driver.Client | None = None,
        pg_conninfo: str = "",
    ):
        self._redis = redis
        self._ch = clickhouse
        self._pg_conninfo = pg_conninfo

    async def store(self, result: SafetyEngineResult) -> None:
        """Write result to all stores (best-effort for each)."""
        await self._write_redis(result)
        await self._write_clickhouse(result)

        if result.threat_level in (ThreatLevel.high, ThreatLevel.critical) or result.campaign_alert:
            await self._create_incident(result)

    async def _write_redis(self, result: SafetyEngineResult) -> None:
        """Cache latest safety score in Redis (60s TTL)."""
        if not self._redis:
            return
        try:
            key = f"safety_score:{result.client_id}:{result.agent_id}"
            value = json.dumps({
                "safety_score": result.safety_score,
                "threat_level": result.threat_level.value,
                "block_recommended": result.block_recommended,
                "campaign_alert": result.campaign_alert,
                "detection_count": len(result.detections),
                "updated_at": datetime.utcnow().isoformat(),
            })
            self._redis.setex(key, 60, value)
        except Exception:
            logger.warning("Failed to write safety score to Redis", exc_info=True)

    async def _write_clickhouse(self, result: SafetyEngineResult) -> None:
        """Insert event row into ClickHouse trust_events table."""
        if not self._ch:
            return
        try:
            self._ch.insert(
                "trust_events",
                [[
                    result.event_id,
                    result.client_id,
                    result.agent_id,
                    datetime.utcnow(),
                    result.safety_score,
                    1 if result.block_recommended else 0,
                    result.threat_level.value,
                    json.dumps([d.model_dump() for d in result.detections]),
                ]],
                column_names=[
                    "event_id", "client_id", "agent_id", "timestamp",
                    "safety_score", "safety_alert_triggered", "alert_type",
                    "raw_payload",
                ],
            )
        except Exception:
            logger.error("Failed to write to ClickHouse", exc_info=True)

    async def _create_incident(self, result: SafetyEngineResult) -> None:
        """Create a safety incident in PostgreSQL if severity >= high."""
        if not self._pg_conninfo:
            return
        try:
            import psycopg

            severity = "critical" if result.campaign_alert else result.threat_level.value
            title = self._incident_title(result)
            evidence = {
                "safety_score": result.safety_score,
                "detections": [d.model_dump() for d in result.detections],
                "llm_judge": result.llm_judge_review.model_dump(),
                "campaign_alert": result.campaign_alert,
            }

            # Generate incident ID: INC-YYYY-NNN
            year = datetime.utcnow().year
            async with await psycopg.AsyncConnection.connect(self._pg_conninfo) as conn, conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM incidents WHERE id LIKE %s",
                    (f"INC-{year}-%",),
                )
                row = await cur.fetchone()
                count = (row[0] if row else 0) + 1
                incident_id = f"INC-{year}-{count:03d}"

                await cur.execute(
                    """INSERT INTO incidents (id, client_id, agent_id, engine, severity, title, description, evidence, engine_score_at_incident, status)
                    VALUES (%s, %s, %s, 'safety', %s, %s, %s, %s, %s, 'open')
                    ON CONFLICT (id) DO NOTHING""",
                    (
                        incident_id,
                        result.client_id,
                        result.agent_id,
                        severity,
                        title,
                        f"Safety score {result.safety_score}/100 — {len(result.detections)} detection(s)",
                        json.dumps(evidence),
                        result.safety_score,
                    ),
                )
                await conn.commit()

            logger.info("Created incident %s for event %s", incident_id, result.event_id)
        except Exception:
            logger.error("Failed to create incident in PostgreSQL", exc_info=True)

    @staticmethod
    def _incident_title(result: SafetyEngineResult) -> str:
        if result.campaign_alert:
            return f"Coordinated attack campaign on agent {result.agent_id[:8]}"
        detection_types = {d.type.value for d in result.detections}
        types_str = ", ".join(sorted(detection_types))
        return f"Safety violation ({types_str}) — score {result.safety_score}"
