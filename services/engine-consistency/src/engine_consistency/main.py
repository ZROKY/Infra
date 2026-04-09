import logging
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI

from .config import settings
from .engine import ConsistencyEngine
from .routes.analyze import router as analyze_router
from .routes.health import router as health_router
from .storage import ConsistencyStorage
from .worker import ConsistencyWorker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────
    redis_client = None
    ch_client = None
    worker = None

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

    engine = ConsistencyEngine(redis_client=redis_client)
    storage = ConsistencyStorage(redis_client=redis_client, clickhouse_client=ch_client)
    worker = ConsistencyWorker(engine=engine, storage=storage)

    app.state.engine = engine
    app.state.storage = storage
    app.state.worker = worker

    try:
        worker.start()
    except Exception:
        logger.warning("Pub/Sub worker failed to start — running API-only mode")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────
    if worker:
        worker.stop()
    if redis_client:
        redis_client.close()
    if ch_client:
        ch_client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="ZROKY engine-consistency",
        description="Behavioral drift, regression testing, benchmarking",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router, tags=["System"])
    app.include_router(analyze_router, tags=["Analysis"])
    return app
