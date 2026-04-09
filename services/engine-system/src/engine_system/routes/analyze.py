"""POST /analyze endpoint for direct system evaluation."""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..models import SystemEngineResult, SystemEventInput

router = APIRouter()


@router.post("/analyze", response_model=SystemEngineResult)
async def analyze_event(event: SystemEventInput, request: Request) -> SystemEngineResult:
    engine = request.app.state.engine
    storage = request.app.state.storage
    result = await engine.analyze(event)
    await storage.store(result)
    return result
