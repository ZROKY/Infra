import logging
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI

from .config import settings
from .engine import TrustScoreEngine
from .routes.compute import router as compute_router
from .routes.health import router as health_router
from .storage import TrustStorage

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────
    redis_client = None
    ch_client = None

    try:
        redis_client = redis.from_url(settings.redis_url, decode_responses=False)
        redis_client.ping()
        logger.info("Redis connected")
    except Exception:
        logger.warning("Redis unavailable — running without cache")
        redis_client = None

    try:
        import clickhouse_connect
        ch_client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_database,
        )
        logger.info("ClickHouse connected")
    except Exception:
        logger.warning("ClickHouse unavailable — running without analytics storage")
        ch_client = None

    engine = TrustScoreEngine(redis_client=redis_client)
    storage = TrustStorage(redis_client=redis_client, clickhouse_client=ch_client)

    app.state.engine = engine
    app.state.storage = storage

    yield

    # ── Shutdown ───────────────────────────────────────────────────────
    if redis_client:
        redis_client.close()
    if ch_client:
        ch_client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="ZROKY trust-computer",
        description="Weighted Trust Score aggregation, overrides, status bands",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router, tags=["System"])
    app.include_router(compute_router, tags=["Trust Score"])
    return app
