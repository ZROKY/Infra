"""POST /analyze endpoint for direct grounding evaluation."""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..models import GroundingEngineResult, GroundingEventInput

router = APIRouter()


@router.post("/analyze", response_model=GroundingEngineResult)
async def analyze_event(event: GroundingEventInput, request: Request) -> GroundingEngineResult:
    engine = request.app.state.engine
    storage = request.app.state.storage
    result = await engine.analyze(event)
    await storage.store(result)
    return result
