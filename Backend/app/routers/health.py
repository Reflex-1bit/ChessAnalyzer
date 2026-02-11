from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "Chess Coach AI API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "games": "/api/games",
            "analytics": "/api/analytics",
            "puzzles": "/api/recommendations/puzzles",
            "daily_puzzle": "/api/recommendations/puzzles/daily"
        }
    }


@router.get("/health")
async def health():
    return {"status": "ok", "db": settings.database_url, "mode": "heuristic"}


@router.get("/info")
async def info():
    return {
        "service": "Chess Coach AI - heuristic mode",
        "database": settings.database_url,
        "stockfish_required": False,
        "ml": "disabled (no TensorFlow)",
    }
