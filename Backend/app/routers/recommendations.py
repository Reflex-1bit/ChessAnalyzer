"""
Recommendation endpoints (puzzles, improvements)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_session
from app.services.lichess import get_lichess_service

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class PuzzleRecommendation(BaseModel):
    puzzle_id: str
    theme: Optional[str] = None
    themes: Optional[List[str]] = None
    rating: Optional[int] = None
    url: Optional[str] = None
    fen: Optional[str] = None
    solution: Optional[List[str]] = None
    pgn: Optional[str] = None
    initialPly: Optional[int] = None
    isTrainingLink: Optional[bool] = False


class PuzzleRecommendationResponse(BaseModel):
    puzzles: List[PuzzleRecommendation]
    count: int


class PuzzleDetailResponse(BaseModel):
    puzzle_id: str
    rating: int
    themes: List[str]
    fen: str
    solution: List[str]
    url: str
    pgn: Optional[str] = None
    initialPly: Optional[int] = None


@router.get("/puzzles", response_model=PuzzleRecommendationResponse)
async def get_puzzle_recommendations(
    themes: Optional[str] = None,
    limit: int = 5,
    session: AsyncSession = Depends(get_session),
):
    """
    Get puzzle recommendations based on weaknesses
    
    Themes can be: tactics, endgame, middlegame, opening, etc.
    Multiple themes can be comma-separated: "tactics,endgame"
    
    Returns complete puzzle data including FEN and solution for interactive play.
    """
    # Parse themes
    theme_list = [t.strip() for t in themes.split(",")] if themes else None
    
    # Get Lichess service
    lichess = await get_lichess_service()
    
    try:
        puzzles = await lichess.recommend_puzzles(themes=theme_list, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch puzzles from Lichess: {str(e)}"
        )
    
    # Format response with complete puzzle data
    puzzle_recommendations = []
    for puzzle in puzzles:
        puzzle_id = str(puzzle.get("id") or puzzle.get("puzzleId", ""))
        puzzle_recommendations.append(
            PuzzleRecommendation(
                puzzle_id=puzzle_id,
                theme=puzzle.get("theme"),
                themes=puzzle.get("themes", []),
                rating=puzzle.get("rating"),
                url=puzzle.get("url") or f"https://lichess.org/training/{puzzle_id}",
                fen=puzzle.get("fen"),
                solution=puzzle.get("solution", []),
                pgn=puzzle.get("pgn"),
                initialPly=puzzle.get("initialPly"),
                isTrainingLink=puzzle.get("isTrainingLink", False),
            )
        )
    
    return PuzzleRecommendationResponse(
        puzzles=puzzle_recommendations,
        count=len(puzzle_recommendations)
    )


@router.get("/puzzles/daily")
async def get_daily_puzzle():
    """
    Get today's Lichess daily puzzle
    Returns complete puzzle data for interactive play
    """
    lichess = await get_lichess_service()
    
    try:
        puzzle = await lichess.get_daily_puzzle()
        if not puzzle:
            raise HTTPException(status_code=404, detail="Could not fetch daily puzzle")
        
        return PuzzleDetailResponse(
            puzzle_id=str(puzzle.get("id", "")),
            rating=puzzle.get("rating", 1500),
            themes=puzzle.get("themes", []),
            fen=puzzle.get("fen", ""),
            solution=puzzle.get("solution", []),
            url=puzzle.get("url", ""),
            pgn=puzzle.get("pgn"),
            initialPly=puzzle.get("initialPly"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch daily puzzle: {str(e)}"
        )


@router.get("/puzzles/{puzzle_id}")
async def get_puzzle_by_id(puzzle_id: str):
    """
    Get a specific puzzle by its Lichess ID
    Returns complete puzzle data for interactive play
    """
    lichess = await get_lichess_service()
    
    try:
        puzzle = await lichess.get_puzzle_by_id(puzzle_id)
        if not puzzle:
            raise HTTPException(status_code=404, detail=f"Puzzle {puzzle_id} not found")
        
        return PuzzleDetailResponse(
            puzzle_id=str(puzzle.get("id", puzzle_id)),
            rating=puzzle.get("rating", 1500),
            themes=puzzle.get("themes", []),
            fen=puzzle.get("fen", ""),
            solution=puzzle.get("solution", []),
            url=puzzle.get("url", f"https://lichess.org/training/{puzzle_id}"),
            pgn=puzzle.get("pgn"),
            initialPly=puzzle.get("initialPly"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch puzzle: {str(e)}"
        )


@router.get("/puzzles/weaknesses/{game_id}")
async def get_puzzles_for_weaknesses(
    game_id: int,
    limit: int = 5,
    session: AsyncSession = Depends(get_session),
):
    """
    Get puzzle recommendations based on weaknesses detected in a game
    
    Analyzes the game's mistakes and recommends puzzles targeting those weaknesses
    """
    from app.models import Game
    from app.services.game_analyzer import GameAnalyzer
    from sqlalchemy import select
    
    # Get game
    result = await session.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if not game.pgn:
        raise HTTPException(status_code=400, detail="Game has no PGN data")
    
    # Analyze game to get mistakes
    analyzer = GameAnalyzer()
    analysis = await analyzer.analyze_game(game, game.pgn)
    
    # Determine weakness themes based on mistakes
    themes = []
    
    if analysis.get("blunders", 0) > 0:
        themes.append("tactics")  # Blunders often due to tactical mistakes
        themes.append("defense")  # Need better defensive tactics
    
    if analysis.get("mistakes", 0) > 0:
        themes.append("middlegame")  # Mistakes often in middlegame
        themes.append("tactics")
    
    if analysis.get("inaccuracies", 0) > 0:
        themes.append("positional")  # Inaccuracies often positional
    
    # Check if mistakes are in endgame (simplified check)
    moves = analysis.get("moves", [])
    endgame_mistakes = sum(1 for m in moves if m.get("move_number", 0) > 30 and (m.get("is_blunder") or m.get("is_mistake")))
    if endgame_mistakes > 0:
        themes.append("endgame")
    
    # Default themes if none found
    if not themes:
        themes = ["tactics", "endgame", "middlegame"]
    
    # Remove duplicates
    themes = list(dict.fromkeys(themes))[:3]  # Max 3 themes
    
    lichess = await get_lichess_service()
    
    try:
        puzzles = await lichess.recommend_puzzles(themes=themes, limit=limit)
    except Exception as e:
        print(f"Error fetching puzzles: {e}")
        # Return empty puzzles on error
        puzzles = []
    
    puzzle_recommendations = []
    for puzzle in puzzles:
        puzzle_id = str(puzzle.get("id") or puzzle.get("puzzleId", "") or f"puzzle-{len(puzzle_recommendations)}")
        puzzle_theme = puzzle.get("theme")
        puzzle_themes = puzzle.get("themes", [])
        
        if not puzzle_theme:
            if isinstance(puzzle_themes, list) and puzzle_themes:
                puzzle_theme = puzzle_themes[0]
            else:
                puzzle_theme = themes[0] if themes else "tactics"
        
        puzzle_url = puzzle.get("url")
        if not puzzle_url:
            puzzle_url = f"https://lichess.org/training/{puzzle_theme}"
        
        # Include complete puzzle data for interactive play
        puzzle_recommendations.append({
            "puzzle_id": puzzle_id,
            "theme": str(puzzle_theme),
            "themes": puzzle_themes if isinstance(puzzle_themes, list) else [puzzle_theme],
            "rating": puzzle.get("rating", 1500),
            "url": puzzle_url,
            "fen": puzzle.get("fen"),
            "solution": puzzle.get("solution", []),
            "pgn": puzzle.get("pgn"),
            "initialPly": puzzle.get("initialPly"),
            "isTrainingLink": puzzle.get("isTrainingLink", False),
        })
    
    return {
        "game_id": game_id,
        "puzzles": puzzle_recommendations,
        "count": len(puzzle_recommendations),
        "themes": themes,
        "weaknesses": {
            "blunders": analysis.get("blunders", 0),
            "mistakes": analysis.get("mistakes", 0),
            "inaccuracies": analysis.get("inaccuracies", 0),
        }
    }
