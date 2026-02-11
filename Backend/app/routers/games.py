"""
Game management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db import get_session
from app.models import Game, User, Move
from app.services.chess_com import get_chess_com_service
from app.services.pgn_parser import parse_pgn
from app.services.game_analyzer import GameAnalyzer
import chess

router = APIRouter(prefix="/api/games", tags=["games"])


class GameResponse(BaseModel):
    id: int
    chess_com_url: Optional[str]
    white_player: str
    black_player: str
    result: Optional[str]
    time_control: Optional[str]
    game_type: Optional[str]
    analyzed: bool
    played_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ImportGamesRequest(BaseModel):
    chess_com_username: str
    limit: Optional[int] = 10


class GameImportResponse(BaseModel):
    imported: int
    games: List[GameResponse]


@router.get("", response_model=List[GameResponse])
async def list_games(
    user_id: Optional[int] = None,
    analyzed: Optional[bool] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    """List games"""
    query = select(Game)
    
    if user_id:
        query = query.where(Game.user_id == user_id)
    if analyzed is not None:
        query = query.where(Game.analyzed == analyzed)
    
    query = query.order_by(Game.played_at.desc()).limit(limit)
    
    result = await session.execute(query)
    games = result.scalars().all()
    return games


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific game"""
    result = await session.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game


@router.post("/import", response_model=GameImportResponse)
async def import_games(
    request: ImportGamesRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Import games from Chess.com for a user
    
    Creates a user if they don't exist, then imports their recent games
    """
    # Get or create user
    result = await session.execute(
        select(User).where(User.chess_com_username == request.chess_com_username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            username=request.chess_com_username,
            chess_com_username=request.chess_com_username,
        )
        session.add(user)
        await session.flush()
    
    # Get Chess.com service
    chess_com = await get_chess_com_service()
    
    # Fetch recent games
    try:
        chess_com_games = await chess_com.get_recent_games(
            request.chess_com_username,
            limit=request.limit or 10
        )
        print(f"Fetched {len(chess_com_games)} games from Chess.com")
    except Exception as e:
        print(f"Error fetching games: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch games from Chess.com: {str(e)}"
        )
    
    if not chess_com_games:
        return GameImportResponse(
            imported=0,
            games=[]
        )
    
    imported_games = []
    
    for chess_com_game in chess_com_games:
        print(f"Processing game: {chess_com_game}")
        game_url = chess_com_game.get("url", "") or chess_com_game.get("pgn", "")
        
        # If no URL, try constructing it from game ID or skip
        if not game_url:
            print(f"No URL found for game: {chess_com_game}")
            continue
        
        # Ensure URL is absolute
        if game_url.startswith("/"):
            game_url = f"https://www.chess.com{game_url}"
        elif not game_url.startswith("http"):
            # Might be just a path, try to construct full URL
            game_url = f"https://www.chess.com{game_url}" if game_url.startswith("/") else f"https://www.chess.com/game/{game_url}"
        
        print(f"Game URL: {game_url}")
        
        # Check if game already exists
        result = await session.execute(
            select(Game).where(Game.chess_com_url == game_url)
        )
        existing_game = result.scalar_one_or_none()
        
        # PGN is already in the Chess.com API response!
        pgn = chess_com_game.get("pgn", "")
        
        # If PGN not in response, try fetching it (fallback)
        if not pgn:
            print(f"No PGN in response, trying to fetch for: {game_url}")
            pgn = await chess_com.get_game_pgn(game_url)
            if not pgn and not game_url.endswith('.pgn'):
                pgn = await chess_com.get_game_pgn(f"{game_url}.pgn")
        
        if not pgn:
            print(f"No PGN for game: {game_url}")
            continue
        
        # Check if game already exists by UUID (more reliable than URL)
        game_uuid = chess_com_game.get("uuid", "")
        existing_game = None
        if game_uuid:
            result = await session.execute(
                select(Game).where(Game.chess_com_id == game_uuid)
            )
            existing_game = result.scalar_one_or_none()
        
        # Also check by URL as fallback
        if not existing_game:
            result = await session.execute(
                select(Game).where(Game.chess_com_url == game_url)
            )
            existing_game = result.scalar_one_or_none()
        
        if existing_game:
            print(f"Game already exists, skipping: {game_url}")
            imported_games.append(existing_game)
            continue
        
        # Parse PGN
        game_data = parse_pgn(pgn)
        if not game_data:
            print(f"Failed to parse PGN for game: {game_url}")
            continue
        
        print(f"Parsed game: {game_data.get('white_player')} vs {game_data.get('black_player')}")
        
        # Extract additional info from Chess.com API response
        chess_com_white = chess_com_game.get("white", {}).get("username", game_data["white_player"])
        chess_com_black = chess_com_game.get("black", {}).get("username", game_data["black_player"])
        time_class = chess_com_game.get("time_class", game_data.get("game_type", "rapid"))
        rated_status = chess_com_game.get("rated", game_data.get("rated", False))
        
        # Create game record
        game = Game(
            user_id=user.id,
            chess_com_url=game_url,
            chess_com_id=str(chess_com_game.get("uuid", "") or chess_com_game.get("id", "")),
            white_player=chess_com_white,
            black_player=chess_com_black,
            result=game_data["result"],
            time_control=game_data["time_control"] or chess_com_game.get("time_control", ""),
            game_type=time_class,
            rated=rated_status,
            pgn=pgn,
            fen_start=chess.Board().fen(),
            played_at=game_data["played_at"],
        )
        
        try:
            session.add(game)
            await session.flush()  # Flush to get the ID
            imported_games.append(game)
            print(f"Successfully added game {game.id}: {game.white_player} vs {game.black_player}")
        except Exception as e:
            print(f"Error adding game to database: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    await session.commit()
    print(f"Committed {len(imported_games)} games to database")
    
    # Refresh games to get IDs
    for game in imported_games:
        await session.refresh(game)
    
    return GameImportResponse(
        imported=len(imported_games),
        games=imported_games
    )


@router.post("/{game_id}/analyze")
async def analyze_game(
    game_id: int,
    force: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """
    Analyze a game to detect mistakes
    
    Uses evaluation sources in priority order:
    1. Lichess Cloud API (fast, no local setup needed)
    2. Local Stockfish (if available)
    3. Material heuristic (fallback)
    
    Returns move-by-move analysis with accuracy score.
    
    Args:
        game_id: ID of the game to analyze
        force: If True, re-analyze even if already analyzed
    """
    # Get game
    result = await session.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if not game.pgn:
        raise HTTPException(status_code=400, detail="Game has no PGN data")
    
    # Check if already analyzed - return cached results
    if game.analyzed and not force:
        # Load existing moves from database
        moves_result = await session.execute(
            select(Move).where(Move.game_id == game_id).order_by(Move.move_number, Move.color)
        )
        existing_moves = moves_result.scalars().all()
        
        if existing_moves:
            moves_data = []
            blunders = 0
            mistakes = 0
            inaccuracies = 0
            
            for move in existing_moves:
                move_dict = {
                    "move_number": move.move_number,
                    "color": move.color,
                    "san": move.san,
                    "uci": move.uci,
                    "fen_before": move.fen_before,
                    "fen_after": move.fen_after,
                    "evaluation_before": move.evaluation_before,
                    "evaluation_after": move.evaluation_after,
                    "evaluation_loss": move.evaluation_loss,
                    "best_move": move.best_move,
                    "best_move_eval": move.best_move_eval,
                    "is_blunder": move.is_blunder,
                    "is_mistake": move.is_mistake,
                    "is_inaccuracy": move.is_inaccuracy,
                    "quality": move.quality,
                    "source": move.source,
                }
                moves_data.append(move_dict)
                
                if move.is_blunder:
                    blunders += 1
                if move.is_mistake:
                    mistakes += 1
                if move.is_inaccuracy:
                    inaccuracies += 1
            
            # Calculate accuracy
            total_moves = len(moves_data)
            error_moves = blunders * 3 + mistakes * 2 + inaccuracies
            accuracy = max(0, min(100, 100 - (error_moves / max(total_moves, 1)) * 10))
            
            analysis = {
                "game_id": game_id,
                "total_moves": total_moves,
                "blunders": blunders,
                "mistakes": mistakes,
                "inaccuracies": inaccuracies,
                "accuracy": round(accuracy, 1),
                "moves": moves_data,
                "analysis_source": "cached",
            }
            
            return {
                "game_id": game_id,
                "analysis": analysis,
                "summary": {
                    "total_moves": total_moves,
                    "blunders": blunders,
                    "mistakes": mistakes,
                    "inaccuracies": inaccuracies,
                    "accuracy": round(accuracy, 1),
                    "analysis_source": "cached",
                }
            }
    
    # Analyze game (fresh analysis)
    analyzer = GameAnalyzer()
    analysis = await analyzer.analyze_game(game, game.pgn)
    
    # Save analysis results to Move table
    moves_data = analysis.get("moves", [])
    
    # Delete existing moves for this game (re-analyze)
    from sqlalchemy import delete
    await session.execute(
        delete(Move).where(Move.game_id == game_id)
    )
    
    # Save each move with analysis
    for move_data in moves_data:
        move = Move(
            game_id=game_id,
            move_number=move_data.get("move_number", 0),
            color=move_data.get("color", "w"),
            san=move_data.get("san", ""),
            uci=move_data.get("uci"),
            fen_before=move_data.get("fen_before"),
            fen_after=move_data.get("fen_after"),
            evaluation_before=move_data.get("evaluation_before"),
            evaluation_after=move_data.get("evaluation_after"),
            evaluation_loss=move_data.get("evaluation_loss"),
            best_move=move_data.get("best_move"),
            best_move_eval=move_data.get("best_move_eval"),
            is_blunder=move_data.get("is_blunder", False),
            is_mistake=move_data.get("is_mistake", False),
            is_inaccuracy=move_data.get("is_inaccuracy", False),
            quality=move_data.get("quality"),
            explanation=move_data.get("explanation"),
            source=move_data.get("source"),
        )
        session.add(move)
    
    game.analyzed = True
    game.analyzed_at = datetime.utcnow()
    
    await session.commit()
    
    return {
        "game_id": game_id,
        "analysis": analysis,
        "summary": {
            "total_moves": analysis.get("total_moves", 0),
            "blunders": analysis.get("blunders", 0),
            "mistakes": analysis.get("mistakes", 0),
            "inaccuracies": analysis.get("inaccuracies", 0),
            "accuracy": analysis.get("accuracy", 0),
            "analysis_source": analysis.get("analysis_source", "unknown"),
        }
    }


@router.get("/{game_id}/mistakes")
async def get_game_mistakes(
    game_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get all mistakes from a game"""
    result = await session.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if not game.analyzed:
        raise HTTPException(
            status_code=400,
            detail="Game not analyzed yet. Call /analyze first."
        )
    
    # Re-analyze if needed (in production, load from database)
    analyzer = GameAnalyzer()
    analysis = await analyzer.analyze_game(game, game.pgn)
    
    mistakes = [
        move for move in analysis["moves"]
        if move["is_blunder"] or move["is_mistake"] or move["is_inaccuracy"]
    ]
    
    return {
        "game_id": game_id,
        "mistakes": mistakes,
        "count": len(mistakes),
    }
