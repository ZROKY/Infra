"""Analyze route — direct invocation of Safety Engine for testing/internal use."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..models import SafetyEngineResult, SafetyEventInput

router = APIRouter()


@router.post("/analyze", response_model=SafetyEngineResult)
async def analyze_event(event: SafetyEventInput, request: Request) -> SafetyEngineResult:
    """
    Run Safety Engine analysis on a single event.

    This endpoint is for internal/testing use. In production, events flow
    through Pub/Sub and are processed by the worker automatically.
    """
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Safety Engine not initialized")

    result = await engine.analyze(event)

    # Optionally store result
    storage = getattr(request.app.state, "storage", None)
    if storage:
        await storage.store(result)

    return result
