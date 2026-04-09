import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .routes.analyze import router as analyze_router
from .routes.health import router as health_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start connections and background worker on startup; clean up on shutdown."""
    import redis as redis_lib

    from .engine import GroundingEngine
    from .storage import GroundingStorage

    # ── Redis ──────────────────────────────────────────────────────────
    redis_client = None
    try:
        redis_client = redis_lib.from_url(settings.redis_url, decode_responses=False)
        redis_client.ping()
        logger.info("Redis connected: %s", settings.redis_url)
    except Exception:
        logger.warning("Redis unavailable — caching disabled")
        redis_client = None

    # ── ClickHouse ─────────────────────────────────────────────────────
    ch_client = None
    try:
        import clickhouse_connect

        ch_client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_database,
        )
        logger.info("ClickHouse connected: %s:%d", settings.clickhouse_host, settings.clickhouse_port)
    except Exception:
        logger.warning("ClickHouse unavailable — analytics storage disabled")

    # ── Engine + Storage ───────────────────────────────────────────────
    engine = GroundingEngine(redis_client=redis_client)
    storage = GroundingStorage(redis_client=redis_client, clickhouse_client=ch_client)

    app.state.engine = engine
    app.state.storage = storage

    # ── Pub/Sub Worker (skip in test) ──────────────────────────────────
    worker = None
    if settings.environment != "test":
        try:
            from .worker import GroundingWorker

            worker = GroundingWorker(engine=engine, storage=storage)
            worker.start()
        except Exception:
            logger.warning("Pub/Sub worker failed to start — running in API-only mode")

    yield

    # ── Cleanup ────────────────────────────────────────────────────────
    if worker:
        worker.stop()
    if redis_client:
        redis_client.close()
    if ch_client:
        ch_client.close()
    logger.info("Grounding engine shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ZROKY engine-grounding",
        description="RAG quality, hallucination detection, claim attribution",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router, tags=["System"])
    app.include_router(analyze_router, tags=["Grounding"])
    return app
