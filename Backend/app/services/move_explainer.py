"""
Intelligent move explanation service.

Generates meaningful, context-aware explanations for chess moves
based on position analysis, piece activity, threats, and tactical motifs.
"""
import chess
from typing import Dict, List, Optional, Tuple


class MoveExplainer:
    """Generate intelligent explanations for chess moves"""
    
    # Piece names for readable output
    PIECE_NAMES = {
        chess.PAWN: "pawn",
        chess.KNIGHT: "knight", 
        chess.BISHOP: "bishop",
        chess.ROOK: "rook",
        chess.QUEEN: "queen",
        chess.KING: "king",
    }
    
    def explain_move(
        self,
        fen_before: str,
        fen_after: str,
        move_san: str,
        move_uci: str,
        quality: str,
        eval_before: float,
        eval_after: float,
        best_move: Optional[str] = None,
        is_player_move: bool = True,
    ) -> Dict:
        """
        Generate a comprehensive explanation for a move.
        
        Returns:
            Dict with 'simple' and 'advanced' explanations, plus tactical info
        """
        try:
            board_before = chess.Board(fen_before)
            board_after = chess.Board(fen_after)
            
            # Parse the move
            move = chess.Move.from_uci(move_uci)
            
            # Analyze the position and move
            analysis = self._analyze_move(board_before, board_after, move, quality)
            
            # Calculate eval difference
            eval_loss = eval_before - eval_after
            eval_loss_pawns = abs(eval_loss) / 100
            
            # Generate explanations based on quality
            simple, advanced = self._generate_explanation(
                analysis, quality, eval_loss_pawns, best_move, move_san
            )
            
            return {
                "simple": simple,
                "advanced": advanced,
                "tactical_motifs": analysis.get("tactics", []),
                "positional_factors": analysis.get("positional", []),
                "threats_created": analysis.get("threats_created", []),
                "threats_missed": analysis.get("threats_missed", []),
            }
            
        except Exception as e:
            print(f"Error explaining move: {e}")
            return {
                "simple": f"Move {move_san} played.",
                "advanced": f"The move {move_san} was played in this position.",
                "tactical_motifs": [],
                "positional_factors": [],
            }
    
    def _analyze_move(
        self, 
        board_before: chess.Board, 
        board_after: chess.Board, 
        move: chess.Move,
        quality: str
    ) -> Dict:
        """Analyze the move for tactical and positional elements"""
        analysis = {
            "tactics": [],
            "positional": [],
            "threats_created": [],
            "threats_missed": [],
            "is_capture": False,
            "is_check": False,
            "is_castling": False,
            "is_promotion": False,
            "piece_moved": None,
            "piece_captured": None,
            "is_sacrifice": False,
            "controls_center": False,
            "develops_piece": False,
            "attacks_king": False,
        }
        
        # Basic move info
        piece_moved = board_before.piece_at(move.from_square)
        piece_captured = board_before.piece_at(move.to_square)
        
        if piece_moved:
            analysis["piece_moved"] = self.PIECE_NAMES.get(piece_moved.piece_type, "piece")
        
        # Capture analysis
        if piece_captured:
            analysis["is_capture"] = True
            analysis["piece_captured"] = self.PIECE_NAMES.get(piece_captured.piece_type, "piece")
            
            # Check if it's a good/bad trade
            piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, 
                          chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
            if piece_moved:
                value_gained = piece_values.get(piece_captured.piece_type, 0)
                value_lost = piece_values.get(piece_moved.piece_type, 0)
                if value_gained > value_lost:
                    analysis["tactics"].append("winning_exchange")
                elif value_gained < value_lost and quality not in ["brilliant", "great", "best"]:
                    analysis["tactics"].append("losing_exchange")
        
        # Check detection
        if board_after.is_check():
            analysis["is_check"] = True
            analysis["tactics"].append("check")
            
            # Checkmate?
            if board_after.is_checkmate():
                analysis["tactics"].append("checkmate")
        
        # Castling
        if board_before.is_castling(move):
            analysis["is_castling"] = True
            analysis["positional"].append("castling")
            if move.to_square in [chess.G1, chess.G8]:
                analysis["positional"].append("kingside_castle")
            else:
                analysis["positional"].append("queenside_castle")
        
        # Promotion
        if move.promotion:
            analysis["is_promotion"] = True
            promoted_to = self.PIECE_NAMES.get(move.promotion, "queen")
            analysis["tactics"].append(f"promotion_to_{promoted_to}")
        
        # Center control (d4, d5, e4, e5)
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        if move.to_square in center_squares:
            analysis["controls_center"] = True
            analysis["positional"].append("center_control")
        
        # Development (knights and bishops moving off back rank)
        back_rank = [chess.A1, chess.B1, chess.C1, chess.D1, chess.E1, chess.F1, chess.G1, chess.H1,
                    chess.A8, chess.B8, chess.C8, chess.D8, chess.E8, chess.F8, chess.G8, chess.H8]
        if piece_moved and piece_moved.piece_type in [chess.KNIGHT, chess.BISHOP]:
            if move.from_square in back_rank and move.to_square not in back_rank:
                analysis["develops_piece"] = True
                analysis["positional"].append("development")
        
        # Attacking towards enemy king
        enemy_king_square = board_after.king(not board_before.turn)
        if enemy_king_square:
            # Check if move attacks squares near the king
            king_zone = list(board_after.attacks(enemy_king_square))
            king_zone.append(enemy_king_square)
            
            if move.to_square in king_zone or any(
                sq in king_zone for sq in board_after.attacks(move.to_square)
            ):
                analysis["attacks_king"] = True
                analysis["tactics"].append("king_attack")
        
        # Fork detection
        if piece_moved and piece_moved.piece_type in [chess.KNIGHT, chess.PAWN, chess.QUEEN]:
            attacked_pieces = []
            for sq in board_after.attacks(move.to_square):
                target = board_after.piece_at(sq)
                if target and target.color != piece_moved.color:
                    if target.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                        attacked_pieces.append(target.piece_type)
            if len(attacked_pieces) >= 2:
                analysis["tactics"].append("fork")
        
        # Pin detection (simplified)
        if piece_moved and piece_moved.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            # Check if piece is aligned with enemy king through another piece
            if enemy_king_square:
                direction = self._get_direction(move.to_square, enemy_king_square)
                if direction:
                    # Check for pieces in between
                    between_squares = list(chess.SquareSet.between(move.to_square, enemy_king_square))
                    pieces_between = [board_after.piece_at(sq) for sq in between_squares]
                    enemy_pieces = [p for p in pieces_between if p and p.color != piece_moved.color]
                    if len(enemy_pieces) == 1:
                        analysis["tactics"].append("pin")
        
        # Sacrifice detection
        if quality == "brilliant":
            analysis["is_sacrifice"] = True
            analysis["tactics"].append("sacrifice")
        
        return analysis
    
    def _get_direction(self, from_sq: int, to_sq: int) -> Optional[Tuple[int, int]]:
        """Get direction vector between squares if aligned"""
        from_file, from_rank = chess.square_file(from_sq), chess.square_rank(from_sq)
        to_file, to_rank = chess.square_file(to_sq), chess.square_rank(to_sq)
        
        file_diff = to_file - from_file
        rank_diff = to_rank - from_rank
        
        # Straight lines
        if file_diff == 0 and rank_diff != 0:
            return (0, 1 if rank_diff > 0 else -1)
        if rank_diff == 0 and file_diff != 0:
            return (1 if file_diff > 0 else -1, 0)
        
        # Diagonals
        if abs(file_diff) == abs(rank_diff):
            return (1 if file_diff > 0 else -1, 1 if rank_diff > 0 else -1)
        
        return None
    
    def _generate_explanation(
        self,
        analysis: Dict,
        quality: str,
        eval_loss_pawns: float,
        best_move: Optional[str],
        move_san: str,
    ) -> Tuple[str, str]:
        """Generate simple and advanced explanations"""
        
        piece = analysis.get("piece_moved", "piece")
        tactics = analysis.get("tactics", [])
        positional = analysis.get("positional", [])
        
        # Build explanation based on quality and analysis
        
        if quality == "brilliant":
            simple = self._brilliant_explanation(analysis, move_san)
            advanced = self._brilliant_advanced(analysis, move_san)
            
        elif quality == "great":
            simple = self._great_explanation(analysis, move_san)
            advanced = self._great_advanced(analysis, move_san, tactics)
            
        elif quality == "best":
            simple = self._best_explanation(analysis, move_san)
            advanced = self._best_advanced(analysis, move_san, tactics, positional)
            
        elif quality == "excellent":
            simple = f"Excellent {piece} move! This finds a strong continuation."
            advanced = self._excellent_advanced(analysis, move_san, tactics, positional)
            
        elif quality == "good":
            simple = self._good_explanation(analysis, move_san)
            advanced = self._good_advanced(analysis, move_san, positional)
            
        elif quality == "book":
            simple = f"Standard opening move following established theory."
            advanced = f"This is a well-known theoretical move. Opening preparation helps navigate familiar positions efficiently."
            
        elif quality == "forced":
            simple = f"This was the only legal move available."
            advanced = f"With only one legal option, {move_san} was forced. The position left no alternatives."
            
        elif quality == "inaccuracy":
            simple = self._inaccuracy_explanation(eval_loss_pawns, best_move)
            advanced = self._inaccuracy_advanced(analysis, eval_loss_pawns, best_move, move_san)
            
        elif quality == "mistake":
            simple = self._mistake_explanation(eval_loss_pawns, best_move)
            advanced = self._mistake_advanced(analysis, eval_loss_pawns, best_move, move_san)
            
        elif quality == "blunder":
            simple = self._blunder_explanation(eval_loss_pawns, best_move, analysis)
            advanced = self._blunder_advanced(analysis, eval_loss_pawns, best_move, move_san)
            
        else:
            simple = f"The {piece} moves to a new square."
            advanced = f"This {piece} move changes the position dynamics."
        
        return simple, advanced
    
    # === BRILLIANT ===
    def _brilliant_explanation(self, analysis: Dict, san: str) -> str:
        if "sacrifice" in analysis.get("tactics", []):
            piece = analysis.get("piece_moved", "piece")
            return f"Brilliant sacrifice! Giving up the {piece} creates a winning attack that's hard to see."
        return f"Brilliant! {san} is an exceptional move finding a hidden winning idea."
    
    def _brilliant_advanced(self, analysis: Dict, san: str) -> str:
        explanations = [f"The move {san} demonstrates deep calculation."]
        if "sacrifice" in analysis.get("tactics", []):
            explanations.append(f"Material is sacrificed for a decisive attack.")
        if "king_attack" in analysis.get("tactics", []):
            explanations.append("The enemy king becomes exposed to dangerous threats.")
        if "fork" in analysis.get("tactics", []):
            explanations.append("Creates a powerful fork winning material back with interest.")
        return " ".join(explanations)
    
    # === GREAT ===
    def _great_explanation(self, analysis: Dict, san: str) -> str:
        if "check" in analysis.get("tactics", []):
            return f"Great move! {san} delivers check while creating strong threats."
        if analysis.get("is_capture"):
            return f"Excellent capture! Taking the {analysis.get('piece_captured', 'piece')} is the best response."
        return f"Great find! {san} is significantly stronger than alternatives."
    
    def _great_advanced(self, analysis: Dict, san: str, tactics: List) -> str:
        parts = [f"{san} stands out as clearly the best move."]
        if "check" in tactics:
            parts.append("The check forces the opponent into a defensive position.")
        if "fork" in tactics:
            parts.append("Multiple pieces are attacked simultaneously.")
        if "pin" in tactics:
            parts.append("A piece is pinned to a more valuable target.")
        parts.append("Alternative moves are significantly weaker.")
        return " ".join(parts)
    
    # === BEST ===
    def _best_explanation(self, analysis: Dict, san: str) -> str:
        if analysis.get("is_castling"):
            side = "kingside" if "kingside_castle" in analysis.get("positional", []) else "queenside"
            return f"Excellent! Castling {side} protects your king and connects your rooks."
        if "checkmate" in analysis.get("tactics", []):
            return f"Checkmate! {san} ends the game."
        if analysis.get("is_capture"):
            return f"Best move! Capturing the {analysis.get('piece_captured', 'piece')} is objectively strongest."
        if analysis.get("develops_piece"):
            return f"Perfect development! The {analysis.get('piece_moved', 'piece')} finds its ideal square."
        return f"This is the engine's top choice - the strongest move in the position."
    
    def _best_advanced(self, analysis: Dict, san: str, tactics: List, positional: List) -> str:
        parts = [f"{san} is the objectively strongest continuation."]
        if "center_control" in positional:
            parts.append("It establishes powerful central control.")
        if "development" in positional:
            parts.append("Piece development is prioritized effectively.")
        if "castling" in positional:
            parts.append("King safety is secured while activating the rook.")
        if "check" in tactics:
            parts.append("The check disrupts opponent's coordination.")
        if not tactics and not positional:
            parts.append("This move maintains optimal piece activity and limits counterplay.")
        return " ".join(parts)
    
    # === EXCELLENT ===
    def _excellent_advanced(self, analysis: Dict, san: str, tactics: List, positional: List) -> str:
        parts = [f"{san} is a very strong move, nearly matching the engine's top choice."]
        if analysis.get("is_capture"):
            parts.append(f"The {analysis.get('piece_captured', 'piece')} capture simplifies favorably.")
        if "center_control" in positional:
            parts.append("Central influence is expanded.")
        return " ".join(parts)
    
    # === GOOD ===
    def _good_explanation(self, analysis: Dict, san: str) -> str:
        piece = analysis.get("piece_moved", "piece")
        if analysis.get("develops_piece"):
            return f"Good development! The {piece} moves to an active square."
        if analysis.get("controls_center"):
            return f"Solid move! Controls important central squares."
        if analysis.get("is_capture"):
            return f"Reasonable capture. Taking the {analysis.get('piece_captured', 'piece')} is sensible."
        return f"A solid {piece} move that maintains the position."
    
    def _good_advanced(self, analysis: Dict, san: str, positional: List) -> str:
        parts = [f"{san} is a reasonable move with no significant drawbacks."]
        if "center_control" in positional:
            parts.append("Central squares remain under influence.")
        if "development" in positional:
            parts.append("Piece activity is improved.")
        if not positional:
            parts.append("The position remains balanced with opportunities for both sides.")
        return " ".join(parts)
    
    # === INACCURACY ===
    def _inaccuracy_explanation(self, loss: float, best: Optional[str]) -> str:
        if best:
            return f"Small inaccuracy losing ~{loss:.1f} pawns of advantage. {best} was more accurate."
        return f"A slight inaccuracy costing about {loss:.1f} pawns. A more precise move existed."
    
    def _inaccuracy_advanced(self, analysis: Dict, loss: float, best: Optional[str], san: str) -> str:
        parts = [f"{san} gives up approximately {loss:.1f} pawns worth of advantage."]
        if best:
            parts.append(f"The engine prefers {best} which maintains better piece coordination.")
        parts.append("While not a serious error, precision at this level matters for converting advantages.")
        return " ".join(parts)
    
    # === MISTAKE ===
    def _mistake_explanation(self, loss: float, best: Optional[str]) -> str:
        if best:
            return f"Mistake! This loses about {loss:.1f} pawns. {best} was much better."
        return f"A significant mistake losing approximately {loss:.1f} pawns of advantage."
    
    def _mistake_advanced(self, analysis: Dict, loss: float, best: Optional[str], san: str) -> str:
        parts = [f"{san} is a clear mistake, dropping about {loss:.1f} pawns."]
        if best:
            parts.append(f"The correct move was {best}.")
        if analysis.get("is_capture"):
            parts.append("This capture loses material or allows a strong response.")
        else:
            parts.append("This move overlooks a tactical opportunity or creates a weakness.")
        return " ".join(parts)
    
    # === BLUNDER ===
    def _blunder_explanation(self, loss: float, best: Optional[str], analysis: Dict) -> str:
        if "checkmate" in str(analysis.get("tactics", [])):
            return f"Blunder! This move allows checkmate. {best} was necessary for survival."
        if loss >= 5:
            return f"Major blunder losing over {loss:.0f} pawns! {best or 'Another move'} was critical."
        if best:
            return f"Blunder losing {loss:.1f} pawns! {best} was essential to hold the position."
        return f"Serious blunder! Approximately {loss:.1f} pawns are lost."
    
    def _blunder_advanced(self, analysis: Dict, loss: float, best: Optional[str], san: str) -> str:
        parts = [f"{san} is a serious error losing approximately {loss:.1f} pawns."]
        if best:
            parts.append(f"The saving move was {best}.")
        
        tactics = analysis.get("tactics", [])
        if "fork" in str(tactics):
            parts.append("This allows a devastating fork.")
        if "pin" in str(tactics):
            parts.append("A crucial pin is created against your pieces.")
        
        parts.append("This type of mistake often decides games at any level.")
        return " ".join(parts)


# Singleton instance
_explainer: Optional[MoveExplainer] = None


def get_move_explainer() -> MoveExplainer:
    """Get or create the move explainer instance"""
    global _explainer
    if _explainer is None:
        _explainer = MoveExplainer()
    return _explainer


def explain_move(
    fen_before: str,
    fen_after: str,
    move_san: str,
    move_uci: str,
    quality: str,
    eval_before: float = 0,
    eval_after: float = 0,
    best_move: Optional[str] = None,
) -> Dict:
    """Convenience function to explain a move"""
    explainer = get_move_explainer()
    return explainer.explain_move(
        fen_before, fen_after, move_san, move_uci,
        quality, eval_before, eval_after, best_move
    )
