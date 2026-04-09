from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "engine-safety",
            "version": "0.1.0",
        },
        "error": None,
    }
