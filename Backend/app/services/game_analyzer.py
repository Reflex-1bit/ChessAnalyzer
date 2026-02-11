"""
Game analysis service using parallel Stockfish for fast, accurate WintrCat classification.

Uses a pool of Stockfish engines to analyze all positions concurrently,
dramatically reducing analysis time from minutes to seconds.
"""
import chess
import chess.pgn
from io import StringIO
from typing import List, Dict, Optional
import time
from app.models import Game, Move, Position
from app.services.stockfish_pool import get_stockfish_pool, StockfishPool
from app.services.pgn_parser import parse_pgn
from app.services.classification import (
    Classification,
    classify_move,
    calculate_accuracy,
    calculate_accuracy_by_color,
    CLASSIFICATION_VALUES,
)
from app.services.move_explainer import explain_move


class GameAnalyzer:
    """Analyze chess games using parallel Stockfish with WintrCat classification"""
    
    def __init__(self, depth: int = 18, pool_size: int = 4, use_lichess_fallback: bool = True):
        """
        Initialize analyzer.
        
        Args:
            depth: Stockfish analysis depth (18 recommended)
            pool_size: Number of parallel Stockfish engines (default 4)
            use_lichess_fallback: If True, try Lichess cloud when Stockfish unavailable
        """
        self.depth = depth
        self.pool_size = pool_size
        self.use_lichess_fallback = use_lichess_fallback
    
    async def analyze_game(self, game: Game, pgn_text: str) -> Dict:
        """
        Analyze a game using parallel Stockfish engines.
        
        This is MUCH faster than sequential analysis because all positions
        are analyzed concurrently.
        """
        start_time = time.time()
        
        # Get the engine pool
        pool = await get_stockfish_pool(pool_size=self.pool_size, depth=self.depth)
        
        if pool.is_available():
            try:
                result = await self._analyze_with_parallel_stockfish(game, pgn_text, pool)
                if "error" not in result and result.get("moves"):
                    elapsed = time.time() - start_time
                    move_count = result['total_moves']
                    accuracy = result['accuracy']
                    print(f"✓ Analyzed {move_count} moves in {elapsed:.1f}s (parallel, depth {self.depth}), accuracy: {accuracy}%")
                    return result
            except Exception as e:
                print(f"Parallel Stockfish analysis failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("WARNING: Stockfish pool not available!")
        
        # Fallback to Lichess cloud
        if self.use_lichess_fallback:
            try:
                from app.services.lichess import get_lichess_service
                lichess = await get_lichess_service()
                result = await lichess.analyze_full_game(pgn_text)
                if result and "error" not in result:
                    result["game_id"] = game.id
                    return result
            except Exception as e:
                print(f"Lichess fallback failed: {e}")
        
        return {"error": "Analysis failed - no engine available"}
    
    async def _analyze_with_parallel_stockfish(
        self, 
        game: Game, 
        pgn_text: str, 
        pool: StockfishPool
    ) -> Dict:
        """
        Analyze game with parallel Stockfish - the fast path!
        
        Strategy:
        1. Parse PGN and collect ALL positions
        2. Send ALL positions to pool for parallel analysis
        3. Classify moves using the results
        """
        # Parse PGN
        pgn = StringIO(pgn_text)
        chess_game = chess.pgn.read_game(pgn)
        
        if chess_game is None:
            return {"error": "Failed to parse PGN"}
        
        # Step 1: Collect all positions and moves
        board = chess_game.board()
        positions = [board.fen()]  # Starting position
        moves_data = []
        move_number = 1
        
        for node in chess_game.mainline():
            move = node.move
            fen_before = board.fen()
            san = board.san(move)
            uci = move.uci()
            color = "w" if board.turn == chess.WHITE else "b"
            legal_moves_count = len(list(board.legal_moves))
            
            board.push(move)
            fen_after = board.fen()
            positions.append(fen_after)
            
            moves_data.append({
                "move_number": move_number,
                "color": color,
                "san": san,
                "uci": uci,
                "fen_before": fen_before,
                "fen_after": fen_after,
                "is_only_legal": legal_moves_count == 1,
            })
            
            if board.turn == chess.WHITE:
                move_number += 1
        
        print(f"Collected {len(positions)} positions, sending to parallel analysis...")
        
        # Step 2: Analyze ALL positions in parallel (the magic happens here!)
        evaluations = await pool.analyze_positions_parallel(positions, depth=self.depth)
        
        # Step 3: Classify each move using the evaluations
        analyzed_moves = []
        
        for i, move_data in enumerate(moves_data):
            eval_before = evaluations[i] if i < len(evaluations) else {}
            eval_after = evaluations[i + 1] if i + 1 < len(evaluations) else {}
            
            # Get evaluations from the mover's perspective
            color_mult = 1 if move_data["color"] == "w" else -1
            
            evaluation_before = eval_before.get("evaluation", 0)
            evaluation_after = eval_after.get("evaluation", 0)
            
            # Convert to mover's perspective
            eval_before_perspective = evaluation_before * color_mult
            eval_after_perspective = -evaluation_after * color_mult  # After move, it's opponent's turn
            
            best_move_uci = eval_before.get("best_move")
            second_best_eval = eval_before.get("second_best_eval")
            if second_best_eval is not None:
                second_best_eval = second_best_eval * color_mult
            
            eval_loss = eval_before_perspective - eval_after_perspective
            
            # Check for mate situations
            is_mate_before = eval_before.get("is_mate", False)
            is_mate_after = eval_after.get("is_mate", False)
            mate_in_before = eval_before.get("mate_in")
            mate_in_after = eval_after.get("mate_in")
            
            if mate_in_after is not None:
                mate_in_after = -mate_in_after  # Flip perspective
            
            # Classify the move
            classification = classify_move(
                move_san=move_data["san"],
                move_uci=move_data["uci"],
                fen_before=move_data["fen_before"],
                fen_after=move_data["fen_after"],
                eval_before=eval_before_perspective,
                eval_after=eval_after_perspective,
                best_move_uci=best_move_uci,
                second_best_eval=second_best_eval,
                is_mate_before=is_mate_before,
                is_mate_after=is_mate_after,
                mate_in_before=mate_in_before,
                mate_in_after=mate_in_after,
                move_number=move_data["move_number"],
                is_only_legal_move=move_data.get("is_only_legal", False),
            )
            
            quality = classification.value
            
            # Generate intelligent explanation for this move
            explanation_data = explain_move(
                fen_before=move_data["fen_before"],
                fen_after=move_data["fen_after"],
                move_san=move_data["san"],
                move_uci=move_data["uci"],
                quality=quality,
                eval_before=eval_before_perspective,
                eval_after=eval_after_perspective,
                best_move=best_move_uci,
            )
            
            analyzed_moves.append({
                "move_number": move_data["move_number"],
                "color": move_data["color"],
                "san": move_data["san"],
                "uci": move_data["uci"],
                "fen_before": move_data["fen_before"],
                "fen_after": move_data["fen_after"],
                "evaluation_before": evaluation_before,
                "evaluation_after": evaluation_after,
                "evaluation_loss": eval_loss,
                "best_move": best_move_uci,
                "best_move_eval": evaluation_before,
                "second_best_eval": second_best_eval,
                "is_blunder": quality == "blunder",
                "is_mistake": quality == "mistake",
                "is_inaccuracy": quality == "inaccuracy",
                "quality": quality,
                "explanation": explanation_data.get("simple", ""),
                "explanation_advanced": explanation_data.get("advanced", ""),
                "tactical_motifs": explanation_data.get("tactical_motifs", []),
                "source": "stockfish",
                "depth": self.depth,
            })
        
        # Calculate statistics
        total_moves = len(analyzed_moves)
        blunders = sum(1 for m in analyzed_moves if m["is_blunder"])
        mistakes = sum(1 for m in analyzed_moves if m["is_mistake"])
        inaccuracies = sum(1 for m in analyzed_moves if m["is_inaccuracy"])
        
        # Count positive classifications
        brilliant = sum(1 for m in analyzed_moves if m["quality"] == "brilliant")
        great = sum(1 for m in analyzed_moves if m["quality"] == "great")
        best = sum(1 for m in analyzed_moves if m["quality"] == "best")
        excellent = sum(1 for m in analyzed_moves if m["quality"] == "excellent")
        good = sum(1 for m in analyzed_moves if m["quality"] == "good")
        book = sum(1 for m in analyzed_moves if m["quality"] == "book")
        forced = sum(1 for m in analyzed_moves if m["quality"] == "forced")
        
        # Calculate accuracy
        accuracies = calculate_accuracy_by_color(analyzed_moves)
        overall_accuracy = calculate_accuracy([m["quality"] for m in analyzed_moves])
        
        return {
            "game_id": game.id,
            "total_moves": total_moves,
            "blunders": blunders,
            "mistakes": mistakes,
            "inaccuracies": inaccuracies,
            "brilliant": brilliant,
            "great": great,
            "best": best,
            "excellent": excellent,
            "good": good,
            "book": book,
            "forced": forced,
            "accuracy": round(overall_accuracy, 1),
            "accuracy_white": accuracies["white"],
            "accuracy_black": accuracies["black"],
            "moves": analyzed_moves,
            "analysis_source": "stockfish",
            "analysis_depth": self.depth,
        }


# Convenience function
async def analyze_game(game: Game, pgn_text: str, depth: int = 18, pool_size: int = 4) -> Dict:
    """
    Analyze a game using parallel Stockfish engines.
    
    Args:
        game: Game model instance
        pgn_text: PGN string of the game
        depth: Analysis depth (18 recommended)
        pool_size: Number of parallel engines (4 recommended)
    
    Returns:
        Analysis results dictionary
    """
    analyzer = GameAnalyzer(depth=depth, pool_size=pool_size)
    return await analyzer.analyze_game(game, pgn_text)
