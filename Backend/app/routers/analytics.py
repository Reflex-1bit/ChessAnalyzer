"""
User analytics endpoints - hyper-specific user data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_session
from app.models import User, Game, Move
from app.services.user_analytics import UserAnalytics
from app.services.skill_analysis import analyze_skills_from_game, analyze_skills_from_multiple_games, get_default_skills

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/user/{username}")
async def get_user_analytics(
    username: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get hyper-specific analytics for a user
    
    Returns detailed insights including:
    - Overall performance statistics
    - Weakness patterns by game phase
    - Opening performance breakdown
    - Time control analysis
    - Color performance (white vs black)
    - Specific improvement recommendations
    """
    # Find user
    result = await session.execute(
        select(User).where(User.chess_com_username == username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    
    # Get analytics
    analytics = await UserAnalytics.get_user_insights(user.id, session)
    
    return analytics


@router.get("/user/{username}/weaknesses")
async def get_user_weaknesses(
    username: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get specific weakness analysis for a user
    
    Returns:
    - Most common mistake types
    - Weakest game phases
    - Problem openings
    - Critical improvement areas
    """
    result = await session.execute(
        select(User).where(User.chess_com_username == username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    
    analytics = await UserAnalytics.get_user_insights(user.id, session)
    
    if "error" in analytics:
        return analytics
    
    return {
        "username": username,
        "weaknesses": analytics.get("weakness_patterns", {}),
        "recommendations": analytics.get("recommendations", {}),
        "critical_stats": {
            "blunder_rate": analytics.get("overall_statistics", {}).get("blunder_rate_percent", 0),
            "weakest_phase": analytics.get("weakness_patterns", {}).get("weakest_game_phase"),
            "blunders_per_game": analytics.get("overall_statistics", {}).get("blunders_per_game", 0),
        }
    }


@router.get("/user/{username}/performance")
async def get_user_performance(
    username: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get performance breakdown by:
    - Opening
    - Time control
    - Color (white/black)
    """
    result = await session.execute(
        select(User).where(User.chess_com_username == username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    
    analytics = await UserAnalytics.get_user_insights(user.id, session)
    
    if "error" in analytics:
        return analytics
    
    return {
        "username": username,
        "opening_performance": analytics.get("opening_performance", {}),
        "time_control_performance": analytics.get("time_control_performance", {}),
        "color_performance": analytics.get("color_performance", {}),
        "total_games": analytics.get("total_games", 0),
    }


@router.get("/user/{username}/skills")
async def get_user_skills(
    username: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get skill profile based on WintrCat analysis.
    
    Returns skill scores for:
    - Opening (first 15 moves performance)
    - Middlegame (moves 15-40 performance)
    - Endgame (late game performance)
    - Tactics (brilliant/great moves vs blunders)
    - Time Management (consistency through the game)
    """
    # Find user
    result = await session.execute(
        select(User).where(User.chess_com_username == username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Return default skills if user not found
        return {
            "username": username,
            "skills": get_default_skills(),
            "games_analyzed": 0,
        }
    
    # Get all analyzed games for user
    games_result = await session.execute(
        select(Game).where(
            Game.user_id == user.id,
            Game.analyzed == True
        ).order_by(Game.played_at.desc()).limit(20)
    )
    games = games_result.scalars().all()
    
    if not games:
        return {
            "username": username,
            "skills": get_default_skills(),
            "games_analyzed": 0,
        }
    
    # Get moves for each game
    all_games_moves = []
    player_color = None
    
    for game in games:
        moves_result = await session.execute(
            select(Move).where(Move.game_id == game.id).order_by(Move.move_number, Move.color)
        )
        moves = moves_result.scalars().all()
        
        if not moves:
            continue
        
        # Determine player color (which side is the connected user)
        if game.white_player and game.white_player.lower() == username.lower():
            player_color = "w"
        elif game.black_player and game.black_player.lower() == username.lower():
            player_color = "b"
        else:
            continue
        
        # Convert to dicts
        moves_data = [
            {
                "move_number": m.move_number,
                "color": m.color,
                "quality": m.quality or "book",
                "is_blunder": m.is_blunder,
                "is_mistake": m.is_mistake,
                "is_inaccuracy": m.is_inaccuracy,
            }
            for m in moves
        ]
        
        # Filter to player's moves
        player_moves = [m for m in moves_data if m["color"] == player_color]
        if player_moves:
            all_games_moves.append(player_moves)
    
    if not all_games_moves:
        return {
            "username": username,
            "skills": get_default_skills(),
            "games_analyzed": 0,
        }
    
    # Calculate skills from all games
    skills = analyze_skills_from_multiple_games(all_games_moves, player_color or "w")
    
    return {
        "username": username,
        "skills": skills,
        "games_analyzed": len(all_games_moves),
    }
