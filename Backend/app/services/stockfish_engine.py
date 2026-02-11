"""
Stockfish chess engine integration with multi-PV support for WintrCat classification.

Provides accurate move classification by analyzing multiple principal variations (PVs)
to determine best move, second-best move, and evaluation differences.
"""
import chess
import chess.engine
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from app.config import settings
import os
import asyncio


class StockfishEngine:
    """Wrapper for Stockfish chess engine with multi-PV support"""
    
    def __init__(self, path: Optional[str] = None, depth: int = 18, multi_pv: int = 2):
        """
        Initialize Stockfish engine.
        
        Args:
            path: Path to Stockfish executable
            depth: Analysis depth (18 recommended for accurate classification)
            multi_pv: Number of principal variations (2+ for brilliant/great detection)
        """
        self.depth = depth
        self.multi_pv = multi_pv
        self.engine_path = path or settings.stockfish_path
        self.engine = None
        self._lock = asyncio.Lock()
        
        if not self.engine_path:
            self.engine_path = self._find_stockfish()
    
    def _find_stockfish(self) -> Optional[str]:
        """Try to find Stockfish in common locations"""
        common_paths = [
            # Windows paths
            r"C:\Program Files\Stockfish\stockfish.exe",
            r"C:\Program Files\Stockfish\stockfish-windows-x86-64-avx2.exe",
            r"C:\Program Files (x86)\Stockfish\stockfish.exe",
            r"C:\stockfish\stockfish.exe",
            r"C:\stockfish\stockfish-windows-x86-64-avx2.exe",
            r".\stockfish.exe",
            r".\stockfish\stockfish.exe",
            r".\backend\stockfish.exe",
            r".\backend\stockfish\stockfish.exe",
            # Linux/Mac paths
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            "/opt/homebrew/bin/stockfish",
            "stockfish",  # If in PATH
        ]
        
        for path in common_paths:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                print(f"Found Stockfish at: {expanded}")
                return expanded
        
        return None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Start the engine"""
        if self.engine_path and os.path.exists(self.engine_path):
            try:
                transport, engine = await chess.engine.popen_uci(self.engine_path)
                self.engine = engine
                print(f"Stockfish engine started successfully at depth {self.depth}, multi-PV {self.multi_pv}")
            except Exception as e:
                print(f"Warning: Could not start Stockfish at {self.engine_path}: {e}")
                self.engine = None
        else:
            paths_tried = self.engine_path or "No path configured"
            print(f"Warning: Stockfish not found. Tried: {paths_tried}")
            print("Please download Stockfish from https://stockfishchess.org/download/")
            print("And set STOCKFISH_PATH in your environment or .env file")
            self.engine = None
    
    async def close(self):
        """Close the engine"""
        if self.engine:
            try:
                await self.engine.quit()
            except Exception as e:
                print(f"Error closing engine: {e}")
            self.engine = None
    
    async def evaluate_position(
        self, 
        board: chess.Board, 
        depth: Optional[int] = None,
        multi_pv: Optional[int] = None
    ) -> Dict:
        """
        Evaluate a position with multi-PV support.
        
        Returns:
            Dict with keys:
                - evaluation: centipawns (from side to move's perspective)
                - best_move: UCI string of best move
                - best_line: list of UCI moves in the best line
                - second_best_eval: evaluation of second-best move (if multi_pv >= 2)
                - second_best_move: UCI string of second-best move
                - is_mate: True if position has forced mate
                - mate_in: Number of moves to mate (positive = side to move wins)
                - depth: analysis depth used
        """
        if not self.engine:
            return self._heuristic_evaluate(board)
        
        async with self._lock:
            try:
                depth_to_use = depth or self.depth
                pv_count = multi_pv or self.multi_pv
                
                # Analyze with multiple principal variations
                infos = await self.engine.analyse(
                    board, 
                    chess.engine.Limit(depth=depth_to_use),
                    multipv=pv_count
                )
                
                # Handle both single result and list of results
                if not isinstance(infos, list):
                    infos = [infos]
                
                if not infos:
                    return self._heuristic_evaluate(board)
                
                # First PV (best move)
                first_info = infos[0]
                score = first_info.get("score")
                
                if score is None:
                    return self._heuristic_evaluate(board)
                
                # Get POV score (from side to move's perspective)
                pov_score = score.relative
                
                # Convert score to centipawns
                is_mate = pov_score.is_mate()
                mate_in = None
                
                if is_mate:
                    mate_in = pov_score.mate()
                    # Use large values for mate scores
                    if mate_in > 0:
                        centipawns = 10000 - (mate_in * 10)  # Faster mate = higher score
                    else:
                        centipawns = -10000 - (mate_in * 10)  # Getting mated
                else:
                    centipawns = pov_score.score() or 0
                
                # Best move and line
                best_pv = first_info.get("pv", [])
                best_move_uci = best_pv[0].uci() if best_pv else None
                best_line = [move.uci() for move in best_pv[:5]]
                
                # Second PV (for brilliant/great detection)
                second_best_eval = None
                second_best_move = None
                
                if len(infos) >= 2:
                    second_info = infos[1]
                    second_score = second_info.get("score")
                    
                    if second_score:
                        second_pov = second_score.relative
                        if second_pov.is_mate():
                            second_mate = second_pov.mate()
                            if second_mate > 0:
                                second_best_eval = 10000 - (second_mate * 10)
                            else:
                                second_best_eval = -10000 - (second_mate * 10)
                        else:
                            second_best_eval = second_pov.score() or 0
                        
                        second_pv = second_info.get("pv", [])
                        if second_pv:
                            second_best_move = second_pv[0].uci()
                
                return {
                    "evaluation": centipawns,
                    "depth": depth_to_use,
                    "best_move": best_move_uci,
                    "best_line": best_line,
                    "second_best_eval": second_best_eval,
                    "second_best_move": second_best_move,
                    "is_mate": is_mate,
                    "mate_in": mate_in,
                    "source": "stockfish",
                }
                
            except Exception as e:
                print(f"Error evaluating position: {e}")
                import traceback
                traceback.print_exc()
                return self._heuristic_evaluate(board)
    
    async def find_best_move(self, board: chess.Board, time_limit: float = 1.0) -> Optional[str]:
        """
        Find the best move for a position with a time limit.
        
        Args:
            board: Chess board position
            time_limit: Maximum time in seconds
        
        Returns:
            Best move in UCI notation, or None if unavailable
        """
        if not self.engine:
            return None
        
        async with self._lock:
            try:
                result = await self.engine.play(
                    board, 
                    chess.engine.Limit(time=time_limit)
                )
                return result.move.uci() if result.move else None
            except Exception as e:
                print(f"Error finding best move: {e}")
                return None
    
    def _heuristic_evaluate(self, board: chess.Board) -> Dict:
        """
        Basic heuristic evaluation (material + position) as fallback.
        Used when Stockfish is not available.
        
        NOTE: This is a very rough approximation and will not give accurate
        move classifications. Install Stockfish for proper analysis.
        """
        # Piece values
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0,
        }
        
        # Piece-square bonuses (simplified)
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        extended_center = [chess.C3, chess.D3, chess.E3, chess.F3,
                          chess.C4, chess.F4, chess.C5, chess.F5,
                          chess.C6, chess.D6, chess.E6, chess.F6]
        
        white_material = 0
        black_material = 0
        white_position = 0
        black_position = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values.get(piece.piece_type, 0)
                
                # Position bonus
                pos_bonus = 0
                if square in center_squares:
                    pos_bonus = 20
                elif square in extended_center:
                    pos_bonus = 10
                
                if piece.color == chess.WHITE:
                    white_material += value
                    white_position += pos_bonus
                else:
                    black_material += value
                    black_position += pos_bonus
        
        # Calculate score from white's perspective
        material_diff = white_material - black_material
        position_diff = white_position - black_position
        
        # Flip if black to move (return from side to move's perspective)
        total = material_diff + position_diff
        if board.turn == chess.BLACK:
            total = -total
        
        return {
            "evaluation": total,
            "depth": 0,
            "best_move": None,
            "best_line": [],
            "second_best_eval": None,
            "second_best_move": None,
            "is_mate": False,
            "mate_in": None,
            "source": "heuristic",
        }
    
    def is_available(self) -> bool:
        """Check if Stockfish is available"""
        return self.engine is not None


# Global engine instance
_engine: Optional[StockfishEngine] = None


async def get_stockfish_engine(depth: int = 18, multi_pv: int = 2) -> StockfishEngine:
    """
    Get or create Stockfish engine instance.
    
    Args:
        depth: Analysis depth (default 18 for accurate classification)
        multi_pv: Number of principal variations (default 2 for brilliant/great detection)
    
    Returns:
        StockfishEngine instance
    """
    global _engine
    if _engine is None:
        _engine = StockfishEngine(depth=depth, multi_pv=multi_pv)
        await _engine.start()
    return _engine


async def close_stockfish_engine():
    """Close the global Stockfish engine"""
    global _engine
    if _engine:
        await _engine.close()
        _engine = None
