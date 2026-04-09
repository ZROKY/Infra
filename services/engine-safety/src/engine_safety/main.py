from fastapi import FastAPI

from .config import settings
from .routes.health import router as health_router


def create_app() -> FastAPI:
    """Create and configure the Safety Engine FastAPI application."""
    app = FastAPI(
        title="ZROKY Safety Engine",
        description="Prompt injection, jailbreak, PII, and toxicity detection",
        version="0.1.0",
    )

    app.include_router(health_router, tags=["System"])

    @app.on_event("startup")
    async def startup():
        pass  # DB connections, Pub/Sub subscriptions added in later phases

    return app
