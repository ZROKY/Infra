from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "trust-computer",
            "version": "0.1.0",
        },
        "error": None,
    }
