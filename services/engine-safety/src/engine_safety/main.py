import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .engine import SafetyEngine
from .routes.analyze import router as analyze_router
from .routes.health import router as health_router

logger = logging.getLogger(__name__)


def _connect_redis():
    """Connect to Redis if URL is configured."""
    try:
        import redis
        return redis.Redis.from_url(settings.redis_url, decode_responses=True)
    except Exception:
        logger.warning("Redis not available — campaign/progression detection disabled")
        return None


def _connect_clickhouse():
    """Connect to ClickHouse if configured."""
    try:
        import clickhouse_connect
        return clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_database,
        )
    except Exception:
        logger.warning("ClickHouse not available — event storage disabled")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle: connections + Pub/Sub worker."""
    redis_client = _connect_redis()
    ch_client = _connect_clickhouse()

    engine = SafetyEngine(redis_client=redis_client)
    app.state.engine = engine

    from .storage import SafetyStorage
    storage = SafetyStorage(
        redis=redis_client,
        clickhouse=ch_client,
        pg_conninfo=settings.database_url,
    )
    app.state.storage = storage

    # Start Pub/Sub worker in production (not in test/dev without emulator)
    worker = None
    if settings.environment != "test":
        try:
            from .worker import SafetyWorker
            worker = SafetyWorker(engine=engine, storage=storage)
            worker.start()
        except Exception:
            logger.warning("Pub/Sub worker failed to start — running without subscription", exc_info=True)

    yield

    # Shutdown
    if worker:
        worker.stop()
    if redis_client:
        redis_client.close()
    if ch_client:
        ch_client.close()


def create_app() -> FastAPI:
    """Create and configure the Safety Engine FastAPI application."""
    app = FastAPI(
        title="ZROKY Safety Engine",
        description="Prompt injection, jailbreak, PII, and toxicity detection",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health_router, tags=["System"])
    app.include_router(analyze_router, tags=["Analysis"])

    return app
