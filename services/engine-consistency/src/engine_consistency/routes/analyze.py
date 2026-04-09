"""POST /analyze endpoint for direct consistency evaluation."""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..models import ConsistencyEngineResult, ConsistencyEventInput

router = APIRouter()


@router.post("/analyze", response_model=ConsistencyEngineResult)
async def analyze_event(event: ConsistencyEventInput, request: Request) -> ConsistencyEngineResult:
    engine = request.app.state.engine
    storage = request.app.state.storage
    result = await engine.analyze(event)
    await storage.store(result)
    return result
