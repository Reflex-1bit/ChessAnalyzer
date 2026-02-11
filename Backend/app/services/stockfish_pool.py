"""
Stockfish Engine Pool for parallel analysis.

Manages multiple Stockfish instances to analyze positions concurrently,
dramatically speeding up game analysis.
"""
import chess
import chess.engine
import asyncio
from typing import Optional, Dict, List, Tuple
from app.config import settings
import os


class StockfishPool:
    """Pool of Stockfish engines for parallel analysis"""
    
    def __init__(
        self, 
        pool_size: int = 4,
        path: Optional[str] = None, 
        depth: int = 18, 
        multi_pv: int = 2
    ):
        """
        Initialize Stockfish engine pool.
        
        Args:
            pool_size: Number of parallel Stockfish instances (default 4)
            path: Path to Stockfish executable
            depth: Analysis depth
            multi_pv: Number of principal variations
        """
        self.pool_size = pool_size
        self.depth = depth
        self.multi_pv = multi_pv
        self.engine_path = path or settings.stockfish_path or self._find_stockfish()
        self.engines: List[chess.engine.UciProtocol] = []
        self.available: asyncio.Queue = asyncio.Queue()
        self._started = False
    
    def _find_stockfish(self) -> Optional[str]:
        """Try to find Stockfish in common locations"""
        common_paths = [
            r"C:\Users\adity\Downloads\stockfish-windows-x86-64\stockfish\stockfish-windows-x86-64.exe",
            r"C:\Program Files\Stockfish\stockfish.exe",
            r"C:\stockfish\stockfish-windows-x86-64-avx2.exe",
            r"C:\stockfish\stockfish.exe",
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            "/opt/homebrew/bin/stockfish",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        return None
    
    async def start(self):
        """Start all engines in the pool"""
        if self._started:
            return
        
        if not self.engine_path or not os.path.exists(self.engine_path):
            print(f"ERROR: Stockfish not found at {self.engine_path}")
            return
        
        print(f"Starting Stockfish pool with {self.pool_size} engines...")
        
        for i in range(self.pool_size):
            try:
                transport, engine = await chess.engine.popen_uci(self.engine_path)
                self.engines.append(engine)
                await self.available.put(engine)
                print(f"  Engine {i+1}/{self.pool_size} started")
            except Exception as e:
                print(f"  Failed to start engine {i+1}: {e}")
        
        self._started = True
        print(f"Stockfish pool ready: {len(self.engines)} engines")
    
    async def close(self):
        """Close all engines"""
        for engine in self.engines:
            try:
                await engine.quit()
            except:
                pass
        self.engines = []
        self._started = False
    
    async def _acquire_engine(self) -> chess.engine.UciProtocol:
        """Get an available engine from the pool"""
        return await self.available.get()
    
    async def _release_engine(self, engine: chess.engine.UciProtocol):
        """Return an engine to the pool"""
        await self.available.put(engine)
    
    async def analyze_position(
        self, 
        fen: str,
        depth: Optional[int] = None,
        multi_pv: Optional[int] = None
    ) -> Dict:
        """Analyze a single position using an available engine"""
        if not self.engines:
            return self._heuristic_evaluate(fen)
        
        engine = await self._acquire_engine()
        try:
            board = chess.Board(fen)
            depth_to_use = depth or self.depth
            pv_count = multi_pv or self.multi_pv
            
            infos = await engine.analyse(
                board,
                chess.engine.Limit(depth=depth_to_use),
                multipv=pv_count
            )
            
            if not isinstance(infos, list):
                infos = [infos]
            
            if not infos:
                return self._heuristic_evaluate(fen)
            
            # Parse first PV (best move)
            first_info = infos[0]
            score = first_info.get("score")
            
            if score is None:
                return self._heuristic_evaluate(fen)
            
            pov_score = score.relative
            is_mate = pov_score.is_mate()
            mate_in = None
            
            if is_mate:
                mate_in = pov_score.mate()
                centipawns = (10000 - abs(mate_in) * 10) * (1 if mate_in > 0 else -1)
            else:
                centipawns = pov_score.score() or 0
            
            best_pv = first_info.get("pv", [])
            best_move_uci = best_pv[0].uci() if best_pv else None
            
            # Second PV for brilliant/great detection
            second_best_eval = None
            if len(infos) >= 2:
                second_info = infos[1]
                second_score = second_info.get("score")
                if second_score:
                    second_pov = second_score.relative
                    if second_pov.is_mate():
                        m = second_pov.mate()
                        second_best_eval = (10000 - abs(m) * 10) * (1 if m > 0 else -1)
                    else:
                        second_best_eval = second_pov.score() or 0
            
            return {
                "fen": fen,
                "evaluation": centipawns,
                "best_move": best_move_uci,
                "second_best_eval": second_best_eval,
                "is_mate": is_mate,
                "mate_in": mate_in,
                "depth": depth_to_use,
                "source": "stockfish",
            }
            
        except Exception as e:
            print(f"Error analyzing position: {e}")
            return self._heuristic_evaluate(fen)
        finally:
            await self._release_engine(engine)
    
    async def analyze_positions_parallel(
        self, 
        fens: List[str],
        depth: Optional[int] = None
    ) -> List[Dict]:
        """
        Analyze multiple positions in parallel.
        
        This is the key speedup - all positions are analyzed concurrently
        using all available engines in the pool.
        """
        if not self.engines:
            print("WARNING: No engines available, using heuristic")
            return [self._heuristic_evaluate(fen) for fen in fens]
        
        print(f"Analyzing {len(fens)} positions in parallel with {len(self.engines)} engines...")
        
        # Create tasks for all positions
        tasks = [
            self.analyze_position(fen, depth)
            for fen in fens
        ]
        
        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error on position {i}: {result}")
                processed_results.append(self._heuristic_evaluate(fens[i]))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _heuristic_evaluate(self, fen: str) -> Dict:
        """Fallback heuristic evaluation"""
        try:
            board = chess.Board(fen)
            piece_values = {
                chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0,
            }
            
            white = sum(
                piece_values.get(board.piece_at(sq).piece_type, 0)
                for sq in chess.SquareSet(board.occupied_co[chess.WHITE])
                if board.piece_at(sq)
            )
            black = sum(
                piece_values.get(board.piece_at(sq).piece_type, 0)
                for sq in chess.SquareSet(board.occupied_co[chess.BLACK])
                if board.piece_at(sq)
            )
            
            score = white - black
            if board.turn == chess.BLACK:
                score = -score
            
            return {
                "fen": fen,
                "evaluation": score,
                "best_move": None,
                "second_best_eval": None,
                "is_mate": False,
                "mate_in": None,
                "depth": 0,
                "source": "heuristic",
            }
        except:
            return {
                "fen": fen,
                "evaluation": 0,
                "best_move": None,
                "second_best_eval": None,
                "is_mate": False,
                "mate_in": None,
                "depth": 0,
                "source": "heuristic",
            }
    
    def is_available(self) -> bool:
        """Check if any engines are available"""
        return len(self.engines) > 0


# Global pool instance
_pool: Optional[StockfishPool] = None


async def get_stockfish_pool(pool_size: int = None, depth: int = None) -> StockfishPool:
    """Get or create the global Stockfish pool"""
    global _pool
    if _pool is None:
        # Use settings if not specified
        actual_pool_size = pool_size or settings.stockfish_pool_size or 4
        actual_depth = depth or settings.stockfish_depth or 18
        _pool = StockfishPool(pool_size=actual_pool_size, depth=actual_depth)
        await _pool.start()
    return _pool


async def close_stockfish_pool():
    """Close the global pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
