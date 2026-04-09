"""Trust Score API routes — compute and query endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..models import TrustScoreInput, TrustScoreResult

router = APIRouter()


@router.post("/compute", response_model=TrustScoreResult)
async def compute_trust_score(input_data: TrustScoreInput, request: Request) -> TrustScoreResult:
    """Compute the unified Trust Score from engine scores."""
    engine = request.app.state.engine
    storage = request.app.state.storage
    result = engine.compute(input_data)
    await storage.store(result)
    return result
