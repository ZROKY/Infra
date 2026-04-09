from fastapi import FastAPI

from .routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="ZROKY trust-computer",
        description="Weighted Trust Score aggregation, overrides, status bands",
        version="0.1.0",
    )
    app.include_router(health_router, tags=["System"])
    return app
