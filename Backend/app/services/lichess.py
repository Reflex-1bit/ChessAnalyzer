"""
Lichess API integration for puzzle recommendations and cloud analysis
"""
import httpx
import asyncio
import random
import chess
import chess.pgn
from io import StringIO
from typing import List, Dict, Optional, Tuple
from app.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential


def get_fen_from_pgn(pgn_text: str, initial_ply: int = 0) -> str:
    """
    Get the FEN position after playing initial_ply half-moves from a PGN.
    """
    try:
        if not pgn_text:
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        
        pgn = StringIO(pgn_text)
        game = chess.pgn.read_game(pgn)
        
        if game is None:
            return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        
        board = game.board()
        
        # Play through the moves up to initial_ply
        moves_played = 0
        for move in game.mainline_moves():
            if moves_played >= initial_ply:
                break
            board.push(move)
            moves_played += 1
        
        return board.fen()
    except Exception as e:
        print(f"Error parsing PGN for FEN: {e}")
        return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class LichessService:
    """Service for interacting with Lichess API"""
    
    BASE_URL = settings.lichess_api_base
    API_TOKEN = settings.lichess_api_token
    RATE_LIMIT_PER_MINUTE = settings.lichess_rate_limit_per_minute
    
    # Lichess puzzle themes mapped to their API names
    PUZZLE_THEMES = {
        "tactics": "short",
        "endgame": "endgame",
        "middlegame": "middlegame",
        "opening": "opening",
        "defense": "defensiveMove",
        "positional": "quietMove",
        "mate": "mate",
        "mateIn1": "mateIn1",
        "mateIn2": "mateIn2",
        "fork": "fork",
        "pin": "pin",
        "skewer": "skewer",
        "discoveredAttack": "discoveredAttack",
        "sacrifice": "sacrifice",
        "deflection": "deflection",
        "interference": "interference",
        "clearance": "clearance",
        "backRankMate": "backRankMate",
        "hangingPiece": "hangingPiece",
        "trappedPiece": "trappedPiece",
        "kingsideAttack": "kingsideAttack",
        "queensideAttack": "queensideAttack",
        "promotion": "promotion",
        "underPromotion": "underPromotion",
        "castling": "castling",
        "enPassant": "enPassant",
        "zugzwang": "zugzwang",
        "attraction": "attraction",
        "crushing": "crushing",
    }
    
    def __init__(self):
        headers = {
            "Accept": "application/json",
        }
        if self.API_TOKEN and self.API_TOKEN != "your_lichess_token_here":
            headers["Authorization"] = f"Bearer {self.API_TOKEN}"
        
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers=headers,
            follow_redirects=True
        )
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_daily_puzzle(self) -> Optional[Dict]:
        """
        Get today's daily puzzle (public endpoint)
        Returns complete puzzle data with FEN and solution
        """
        try:
            response = await self.client.get("/puzzle/daily")
            response.raise_for_status()
            data = response.json()
            
            puzzle_info = data.get("puzzle", {})
            game_info = data.get("game", {})
            
            # Get initial position - compute from PGN if not directly provided
            pgn = game_info.get("pgn", "")
            initial_ply = puzzle_info.get("initialPly", 0)
            fen = game_info.get("fen") or data.get("fen")
            
            # If no FEN provided, compute from PGN
            if not fen and pgn:
                fen = get_fen_from_pgn(pgn, initial_ply)
            
            # Fallback to starting position if nothing works
            if not fen:
                fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            
            return {
                "id": puzzle_info.get("id"),
                "rating": puzzle_info.get("rating", 1500),
                "themes": puzzle_info.get("themes", []),
                "fen": fen,
                "pgn": pgn,
                "solution": puzzle_info.get("solution", []),
                "initialPly": initial_ply,
                "url": f"https://lichess.org/training/{puzzle_info.get('id')}",
            }
        except Exception as e:
            print(f"Error getting daily puzzle: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_puzzle_by_id(self, puzzle_id: str) -> Optional[Dict]:
        """
        Get a specific puzzle by its Lichess ID
        """
        try:
            response = await self.client.get(f"/puzzle/{puzzle_id}")
            response.raise_for_status()
            data = response.json()
            
            puzzle_info = data.get("puzzle", {})
            game_info = data.get("game", {})
            
            # Get initial position - compute from PGN if not directly provided
            pgn = game_info.get("pgn", "")
            initial_ply = puzzle_info.get("initialPly", 0)
            fen = game_info.get("fen") or data.get("fen")
            
            # If no FEN provided, compute from PGN
            if not fen and pgn:
                fen = get_fen_from_pgn(pgn, initial_ply)
            
            # Fallback to starting position if nothing works
            if not fen:
                fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            
            return {
                "id": puzzle_info.get("id"),
                "rating": puzzle_info.get("rating", 1500),
                "themes": puzzle_info.get("themes", []),
                "fen": fen,
                "pgn": pgn,
                "solution": puzzle_info.get("solution", []),
                "initialPly": initial_ply,
                "url": f"https://lichess.org/training/{puzzle_info.get('id')}",
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"Puzzle {puzzle_id} not found")
                return None
            raise
        except Exception as e:
            print(f"Error getting puzzle {puzzle_id}: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_puzzle_activity(self, limit: int = 10) -> List[Dict]:
        """
        Get recent puzzle activity (requires auth token)
        Falls back to daily puzzle if no token
        """
        if not self.API_TOKEN or self.API_TOKEN == "your_lichess_token_here":
            daily = await self.get_daily_puzzle()
            return [daily] if daily else []
        
        try:
            response = await self.client.get(f"/puzzle/activity?max={limit}")
            response.raise_for_status()
            # Lichess returns ndjson for activity
            puzzles = []
            for line in response.text.strip().split("\n"):
                if line:
                    import json
                    puzzles.append(json.loads(line))
            return puzzles[:limit]
        except Exception as e:
            print(f"Error getting puzzle activity: {e}")
            daily = await self.get_daily_puzzle()
            return [daily] if daily else []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_puzzles_by_theme(self, theme: str, difficulty: str = "normal", count: int = 5) -> List[Dict]:
        """
        Get puzzles by theme using Lichess puzzle storm/batch API
        
        Args:
            theme: Puzzle theme (e.g., "fork", "pin", "endgame")
            difficulty: "easiest", "easier", "normal", "harder", "hardest"
            count: Number of puzzles to fetch
        
        Returns:
            List of puzzle dictionaries with FEN and solution moves
        """
        puzzles = []
        
        # Map theme to Lichess API theme
        lichess_theme = self.PUZZLE_THEMES.get(theme.lower(), theme)
        
        try:
            # Try the puzzle batch endpoint (requires recent Lichess API)
            # This endpoint gives us puzzles we can actually solve
            params = {
                "nb": min(count, 50),  # Lichess limits to 50
            }
            
            # Use the puzzle/next endpoint with theme filter
            response = await self.client.get(
                f"/puzzle/next",
                params={"theme": lichess_theme}
            )
            
            if response.status_code == 200:
                data = response.json()
                puzzle_info = data.get("puzzle", {})
                game_info = data.get("game", {})
                
                if puzzle_info:
                    puzzles.append({
                        "id": puzzle_info.get("id"),
                        "rating": puzzle_info.get("rating", 1500),
                        "themes": puzzle_info.get("themes", [theme]),
                        "fen": game_info.get("fen") or data.get("fen"),
                        "pgn": game_info.get("pgn", ""),
                        "solution": puzzle_info.get("solution", []),
                        "initialPly": puzzle_info.get("initialPly", 0),
                        "url": f"https://lichess.org/training/{puzzle_info.get('id')}",
                        "theme": theme,
                    })
        except Exception as e:
            print(f"Error fetching puzzle by theme {theme}: {e}")
        
        # If we couldn't get puzzles from the theme endpoint, use daily as fallback
        if not puzzles:
            daily = await self.get_daily_puzzle()
            if daily:
                daily["theme"] = theme
                puzzles.append(daily)
        
        return puzzles
    
    async def get_random_puzzles(self, rating: int = 1500, limit: int = 5) -> List[Dict]:
        """
        Get random puzzles around a rating from Lichess
        """
        puzzles = []
        
        try:
            # Get daily puzzle first - always available
            daily = await self.get_daily_puzzle()
            if daily:
                puzzles.append(daily)
            
            # Try to get more puzzles using different themes
            themes_to_try = ["fork", "pin", "mate", "endgame", "tactics"]
            for theme in themes_to_try[:limit - 1]:
                theme_puzzles = await self.get_puzzles_by_theme(theme, count=1)
                puzzles.extend(theme_puzzles)
                if len(puzzles) >= limit:
                    break
            
        except Exception as e:
            print(f"Error getting random puzzles: {e}")
        
        return puzzles[:limit]
    
    async def recommend_puzzles(self, themes: List[str] = None, limit: int = 5) -> List[Dict]:
        """
        Recommend puzzles based on weaknesses (themes)
        Returns complete puzzle data with FEN and solution for interactive play
        
        Args:
            themes: List of themes (e.g., ["endgame", "tactics"])
            limit: Number of puzzles to return
        
        Returns:
            List of puzzle recommendations with REAL puzzle data
        """
        puzzles = []
        
        if not themes:
            themes = ["tactics", "endgame", "fork"]
        
        # Always start with the daily puzzle (guaranteed to work)
        try:
            daily = await self.get_daily_puzzle()
            if daily:
                daily["theme"] = themes[0] if themes else "tactics"
                puzzles.append(daily)
        except Exception as e:
            print(f"Error fetching daily puzzle: {e}")
        
        # Get puzzles for each requested theme
        for theme in themes:
            if len(puzzles) >= limit:
                break
            
            try:
                theme_puzzles = await self.get_puzzles_by_theme(theme, count=1)
                for puzzle in theme_puzzles:
                    # Avoid duplicates
                    if not any(p.get("id") == puzzle.get("id") for p in puzzles):
                        puzzles.append(puzzle)
                        if len(puzzles) >= limit:
                            break
            except Exception as e:
                print(f"Error fetching puzzles for theme {theme}: {e}")
                continue
        
        # Fill remaining slots with themed training links if needed
        seen_themes = set()
        for puzzle in puzzles:
            if puzzle.get("theme"):
                seen_themes.add(puzzle["theme"])
        
        # Add training links for themes we couldn't get real puzzles for
        for theme in themes:
            if len(puzzles) >= limit:
                break
            
            if theme not in seen_themes:
                lichess_theme = self.PUZZLE_THEMES.get(theme.lower(), theme)
                puzzles.append({
                    "id": f"training-{lichess_theme}",
                    "rating": 1500,
                    "themes": [theme],
                    "theme": theme,
                    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Default starting position
                    "solution": [],
                    "url": f"https://lichess.org/training/{lichess_theme}",
                    "isTrainingLink": True,  # Flag to indicate this is just a link
                })
                seen_themes.add(theme)
        
        return puzzles[:limit]
    
    # ==================== CLOUD EVALUATION API ====================
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=1, max=5))
    async def get_cloud_eval(self, fen: str, multi_pv: int = 1) -> Optional[Dict]:
        """
        Get cloud evaluation for a position from Lichess.
        Uses Lichess's cached Stockfish evaluations.
        
        Args:
            fen: FEN string of the position
            multi_pv: Number of principal variations to return (1-5)
        
        Returns:
            Dict with evaluation data or None if not available
        """
        try:
            # Use the cloud-eval endpoint (doesn't require auth)
            response = await self.client.get(
                "https://lichess.org/api/cloud-eval",
                params={
                    "fen": fen,
                    "multiPv": min(multi_pv, 5)
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse the evaluation
                pvs = data.get("pvs", [])
                if pvs:
                    first_pv = pvs[0]
                    cp = first_pv.get("cp")  # Centipawns
                    mate = first_pv.get("mate")  # Mate in N
                    moves = first_pv.get("moves", "").split()
                    
                    # Convert mate score to centipawns equivalent
                    if mate is not None:
                        evaluation = 10000 if mate > 0 else -10000
                    elif cp is not None:
                        evaluation = cp
                    else:
                        evaluation = 0
                    
                    return {
                        "fen": data.get("fen", fen),
                        "evaluation": evaluation,
                        "mate": mate,
                        "depth": data.get("depth", 0),
                        "best_move": moves[0] if moves else None,
                        "best_line": moves[:5],
                        "knodes": data.get("knodes", 0),
                        "source": "lichess_cloud"
                    }
            
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Position not in cloud database
                return None
            print(f"HTTP error getting cloud eval: {e}")
            return None
        except Exception as e:
            print(f"Error getting cloud eval for {fen}: {e}")
            return None
    
    async def analyze_game_positions(
        self, 
        positions: List[Dict], 
        delay_between_requests: float = 0.1,
        batch_size: int = 5
    ) -> List[Dict]:
        """
        Analyze multiple positions using Lichess cloud evaluation.
        Uses parallel requests in batches for speed.
        
        Args:
            positions: List of dicts with 'fen', 'move_number', 'color' keys
            delay_between_requests: Delay in seconds between batches (rate limiting)
            batch_size: Number of parallel requests per batch
        
        Returns:
            List of analysis results for each position
        """
        results = [None] * len(positions)
        
        async def evaluate_position(index: int, pos: Dict) -> Tuple[int, Dict]:
            """Evaluate a single position and return with its index"""
            fen = pos.get("fen")
            if not fen:
                return index, {
                    "move_number": pos.get("move_number"),
                    "color": pos.get("color"),
                    "evaluation": 0,
                    "source": "none"
                }
            
            # Get cloud evaluation
            eval_result = await self.get_cloud_eval(fen)
            
            if eval_result:
                return index, {
                    "move_number": pos.get("move_number"),
                    "color": pos.get("color"),
                    "fen": fen,
                    **eval_result
                }
            else:
                # Fallback to basic material evaluation
                material_eval = self._heuristic_evaluate(fen)
                return index, {
                    "move_number": pos.get("move_number"),
                    "color": pos.get("color"),
                    "fen": fen,
                    "evaluation": material_eval,
                    "source": "heuristic"
                }
        
        # Process in batches for faster analysis
        for batch_start in range(0, len(positions), batch_size):
            batch_end = min(batch_start + batch_size, len(positions))
            batch = [(i, positions[i]) for i in range(batch_start, batch_end)]
            
            # Run batch in parallel
            tasks = [evaluate_position(i, pos) for i, pos in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Store results
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"Error in batch evaluation: {result}")
                    continue
                idx, eval_data = result
                results[idx] = eval_data
            
            # Small delay between batches to be nice to Lichess
            if batch_end < len(positions):
                await asyncio.sleep(delay_between_requests)
        
        # Fill any None results with heuristic
        for i, result in enumerate(results):
            if result is None:
                fen = positions[i].get("fen", "")
                results[i] = {
                    "move_number": positions[i].get("move_number"),
                    "color": positions[i].get("color"),
                    "fen": fen,
                    "evaluation": self._heuristic_evaluate(fen) if fen else 0,
                    "source": "heuristic"
                }
        
        return results
    
    def _heuristic_evaluate(self, fen: str) -> int:
        """
        Basic material-based evaluation as fallback.
        Returns evaluation in centipawns from white's perspective.
        """
        try:
            board = chess.Board(fen)
            
            piece_values = {
                chess.PAWN: 100,
                chess.KNIGHT: 320,
                chess.BISHOP: 330,
                chess.ROOK: 500,
                chess.QUEEN: 900,
                chess.KING: 0,
            }
            
            white_material = sum(
                piece_values.get(board.piece_at(sq).piece_type, 0)
                for sq in chess.SquareSet(board.occupied_co[chess.WHITE])
                if board.piece_at(sq)
            )
            
            black_material = sum(
                piece_values.get(board.piece_at(sq).piece_type, 0)
                for sq in chess.SquareSet(board.occupied_co[chess.BLACK])
                if board.piece_at(sq)
            )
            
            return white_material - black_material
        except Exception as e:
            print(f"Error in heuristic evaluation: {e}")
            return 0
    
    async def analyze_full_game(self, pgn_text: str) -> Dict:
        """
        Analyze a full game using Lichess cloud evaluation with WintrCat classification.
        
        Args:
            pgn_text: PGN string of the game
        
        Returns:
            Dict with full game analysis including move-by-move evaluations
        """
        try:
            # Import classification module
            from app.services.classification import (
                classify_move,
                calculate_accuracy,
                calculate_accuracy_by_color,
            )
            
            pgn = StringIO(pgn_text)
            game = chess.pgn.read_game(pgn)
            
            if game is None:
                return {"error": "Failed to parse PGN"}
            
            board = game.board()
            positions = []
            moves_data = []
            move_number = 1
            
            # Collect all positions
            for node in game.mainline():
                move = node.move
                fen_before = board.fen()
                san = board.san(move)
                uci = move.uci()
                color = "w" if board.turn == chess.WHITE else "b"
                
                # Count legal moves for forced detection
                legal_moves_count = len(list(board.legal_moves))
                
                positions.append({
                    "fen": fen_before,
                    "move_number": move_number,
                    "color": color,
                    "legal_moves_count": legal_moves_count,
                })
                
                board.push(move)
                fen_after = board.fen()
                
                moves_data.append({
                    "move_number": move_number,
                    "color": color,
                    "san": san,
                    "uci": uci,
                    "fen_before": fen_before,
                    "fen_after": fen_after,
                    "is_only_legal": legal_moves_count == 1,
                })
                
                # Increment move number after black's move
                if board.turn == chess.WHITE:
                    move_number += 1
            
            # Add final position
            positions.append({
                "fen": board.fen(),
                "move_number": move_number,
                "color": "w" if board.turn == chess.WHITE else "b"
            })
            
            # Get evaluations for all positions (with parallel batching for speed)
            print(f"Analyzing {len(positions)} positions with Lichess cloud (parallel batches)...")
            evaluations = await self.analyze_game_positions(
                positions, 
                delay_between_requests=0.1,  # Short delay between batches
                batch_size=5  # Process 5 positions in parallel
            )
            
            # Combine moves with evaluations using WintrCat classification
            analyzed_moves = []
            blunders = 0
            mistakes = 0
            inaccuracies = 0
            
            for i, move_data in enumerate(moves_data):
                eval_before = evaluations[i] if i < len(evaluations) else {}
                eval_after = evaluations[i + 1] if i + 1 < len(evaluations) else {}
                
                evaluation_before = eval_before.get("evaluation", 0)
                evaluation_after = eval_after.get("evaluation", 0)
                best_move = eval_before.get("best_move")
                
                # Get evaluation from mover's perspective
                color_mult = 1 if move_data["color"] == "w" else -1
                eval_before_perspective = evaluation_before * color_mult
                eval_after_perspective = evaluation_after * color_mult
                eval_loss = eval_before_perspective - eval_after_perspective
                
                # Check for mate situations
                is_mate_before = abs(evaluation_before) >= 9000
                is_mate_after = abs(evaluation_after) >= 9000
                mate_in_before = None
                mate_in_after = None
                
                if is_mate_before:
                    mate_in_before = 1 if evaluation_before > 0 else -1
                    if move_data["color"] == "b":
                        mate_in_before *= -1
                if is_mate_after:
                    mate_in_after = 1 if evaluation_after > 0 else -1
                    if move_data["color"] == "b":
                        mate_in_after *= -1
                
                # Classify using WintrCat algorithm
                classification = classify_move(
                    move_san=move_data["san"],
                    move_uci=move_data["uci"],
                    fen_before=move_data["fen_before"],
                    fen_after=move_data["fen_after"],
                    eval_before=eval_before_perspective,
                    eval_after=eval_after_perspective,
                    best_move_uci=best_move,
                    is_mate_before=is_mate_before,
                    is_mate_after=is_mate_after,
                    mate_in_before=mate_in_before,
                    mate_in_after=mate_in_after,
                    move_number=move_data["move_number"],
                    is_only_legal_move=move_data.get("is_only_legal", False),
                )
                
                quality = classification.value
                is_blunder = quality == "blunder"
                is_mistake = quality == "mistake"
                is_inaccuracy = quality == "inaccuracy"
                
                if is_blunder:
                    blunders += 1
                elif is_mistake:
                    mistakes += 1
                elif is_inaccuracy:
                    inaccuracies += 1
                
                analyzed_moves.append({
                    **move_data,
                    "evaluation_before": evaluation_before,
                    "evaluation_after": evaluation_after,
                    "evaluation_loss": eval_loss,
                    "best_move": best_move,
                    "best_move_eval": eval_before.get("evaluation"),
                    "is_blunder": is_blunder,
                    "is_mistake": is_mistake,
                    "is_inaccuracy": is_inaccuracy,
                    "quality": quality,
                    "source": eval_before.get("source", "lichess_cloud"),
                })
            
            # Calculate accuracy using WintrCat formula
            total_moves = len(analyzed_moves)
            accuracies = calculate_accuracy_by_color(analyzed_moves)
            overall_accuracy = calculate_accuracy([m["quality"] for m in analyzed_moves])
            
            return {
                "total_moves": total_moves,
                "blunders": blunders,
                "mistakes": mistakes,
                "inaccuracies": inaccuracies,
                "accuracy": round(overall_accuracy, 1),
                "accuracy_white": accuracies["white"],
                "accuracy_black": accuracies["black"],
                "moves": analyzed_moves,
                "analysis_source": "lichess_cloud",
            }
            
        except Exception as e:
            print(f"Error analyzing game: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}


# Singleton instance
_lichess_service: Optional[LichessService] = None


async def get_lichess_service() -> LichessService:
    """Get or create Lichess service instance"""
    global _lichess_service
    if _lichess_service is None:
        _lichess_service = LichessService()
    return _lichess_service
