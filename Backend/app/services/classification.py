"""
Move classification service based on WintrCat's algorithm
https://github.com/WintrCat/freechess

Implements the "WTF Algorithm" for dynamic evaluation loss thresholds
"""
import chess
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Classification(Enum):
    """Move classification types"""
    BRILLIANT = "brilliant"
    GREAT = "great"
    BEST = "best"
    EXCELLENT = "excellent"
    GOOD = "good"
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"
    BOOK = "book"
    FORCED = "forced"


# Classification values for accuracy calculation (0-1 scale)
CLASSIFICATION_VALUES = {
    "blunder": 0,
    "mistake": 0.2,
    "inaccuracy": 0.4,
    "good": 0.65,
    "excellent": 0.9,
    "best": 1,
    "great": 1,
    "brilliant": 1,
    "book": 1,
    "forced": 1,
}

# Piece values for sacrifice detection
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: float('inf'),
}


def get_evaluation_loss_threshold(classification: Classification, prev_eval: float) -> float:
    """
    WTF Algorithm - Get the maximum evaluation loss for a classification.
    
    Uses quadratic formulas based on previous position evaluation to determine
    dynamic thresholds that account for position complexity.
    
    Args:
        classification: The classification to get threshold for
        prev_eval: Previous position evaluation in centipawns (absolute value used)
    
    Returns:
        Maximum centipawn loss for this classification to apply
    """
    prev_eval = abs(prev_eval)
    threshold = 0.0
    
    if classification == Classification.BEST:
        # Very tight threshold for best moves
        threshold = 0.0001 * (prev_eval ** 2) + (0.0236 * prev_eval) + 10
    elif classification == Classification.EXCELLENT:
        threshold = 0.0002 * (prev_eval ** 2) + (0.1231 * prev_eval) + 27.5455
    elif classification == Classification.GOOD:
        threshold = 0.0002 * (prev_eval ** 2) + (0.2643 * prev_eval) + 60.5455
    elif classification == Classification.INACCURACY:
        threshold = 0.0002 * (prev_eval ** 2) + (0.3624 * prev_eval) + 108.0909
    elif classification == Classification.MISTAKE:
        threshold = 0.0003 * (prev_eval ** 2) + (0.4027 * prev_eval) + 225.8182
    else:
        threshold = float('inf')
    
    return max(threshold, 0)


def get_attackers(board: chess.Board, square: int) -> List[Tuple[int, chess.PieceType]]:
    """
    Get all pieces attacking a square.
    
    Returns:
        List of (square, piece_type) tuples for attackers
    """
    attackers = []
    piece = board.piece_at(square)
    if not piece:
        return attackers
    
    # Get attackers of opposite color
    opposite_color = not piece.color
    for attacker_square in board.attackers(opposite_color, square):
        attacker = board.piece_at(attacker_square)
        if attacker:
            attackers.append((attacker_square, attacker.piece_type))
    
    return attackers


def get_defenders(board: chess.Board, square: int) -> List[Tuple[int, chess.PieceType]]:
    """
    Get all pieces defending a square.
    
    Returns:
        List of (square, piece_type) tuples for defenders
    """
    defenders = []
    piece = board.piece_at(square)
    if not piece:
        return defenders
    
    # Get defenders of same color
    for defender_square in board.attackers(piece.color, square):
        defender = board.piece_at(defender_square)
        if defender:
            defenders.append((defender_square, defender.piece_type))
    
    return defenders


def is_piece_hanging(last_fen: str, current_fen: str, square: int) -> bool:
    """
    Check if a piece is hanging (can be captured for free or profitably).
    
    Args:
        last_fen: FEN before the move
        current_fen: FEN after the move
        square: Square to check
    
    Returns:
        True if piece is hanging
    """
    try:
        last_board = chess.Board(last_fen)
        board = chess.Board(current_fen)
        
        last_piece = last_board.piece_at(square)
        piece = board.piece_at(square)
        
        if not piece:
            return False
        
        attackers = get_attackers(board, square)
        defenders = get_defenders(board, square)
        
        # If no attackers, piece is not hanging
        if not attackers:
            return False
        
        # If piece was just traded equally or better, not hanging
        if last_piece and last_piece.color != piece.color:
            if PIECE_VALUES.get(last_piece.piece_type, 0) >= PIECE_VALUES.get(piece.piece_type, 0):
                return False
        
        piece_value = PIECE_VALUES.get(piece.piece_type, 0)
        
        # If piece has an attacker of lower value, hanging
        for _, attacker_type in attackers:
            if PIECE_VALUES.get(attacker_type, 0) < piece_value:
                return True
        
        # If more attackers than defenders
        if len(attackers) > len(defenders):
            min_attacker_value = min(
                (PIECE_VALUES.get(t, float('inf')) for _, t in attackers),
                default=float('inf')
            )
            
            # If taking would be a sacrifice itself, not hanging
            if piece_value < min_attacker_value:
                if any(PIECE_VALUES.get(t, 0) < min_attacker_value for _, t in defenders):
                    return False
            
            # If any defender is a pawn, not hanging
            if any(t == chess.PAWN for _, t in defenders):
                return False
            
            return True
        
        return False
        
    except Exception as e:
        print(f"Error checking hanging piece: {e}")
        return False


def classify_move(
    move_san: str,
    move_uci: str,
    fen_before: str,
    fen_after: str,
    eval_before: float,
    eval_after: float,
    best_move_uci: Optional[str],
    second_best_eval: Optional[float] = None,
    is_mate_before: bool = False,
    is_mate_after: bool = False,
    mate_in_before: Optional[int] = None,
    mate_in_after: Optional[int] = None,
    move_number: int = 1,
    is_only_legal_move: bool = False,
) -> Classification:
    """
    Classify a chess move using WintrCat's algorithm.
    
    Args:
        move_san: Move in SAN notation
        move_uci: Move in UCI notation
        fen_before: FEN before move
        fen_after: FEN after move
        eval_before: Evaluation before move (centipawns, from mover's perspective)
        eval_after: Evaluation after move (centipawns, from mover's perspective)
        best_move_uci: Best move according to engine (UCI)
        second_best_eval: Evaluation of second best move (from mover's perspective)
        is_mate_before: If there was mate on board before
        is_mate_after: If there is mate on board after
        mate_in_before: Mate in N before (positive = mover winning)
        mate_in_after: Mate in N after
        move_number: Current move number
        is_only_legal_move: If this was the only legal move
    
    Returns:
        Classification for the move
    """
    try:
        board_before = chess.Board(fen_before)
        board_after = chess.Board(fen_after)
        
        # Calculate evaluation loss (positive = move was worse than best)
        eval_loss = eval_before - eval_after
        
        # If this was the only legal move, it's forced
        if is_only_legal_move:
            return Classification.FORCED
        
        # Book moves for early opening (if move is reasonable)
        if move_number <= 5:
            threshold = get_evaluation_loss_threshold(Classification.GOOD, eval_before)
            if eval_loss <= threshold:
                return Classification.BOOK
        
        # Check if this was the best move
        is_best_move = (best_move_uci and move_uci == best_move_uci)
        
        classification = None
        
        # Handle non-mate situations with standard thresholds
        if not is_mate_before and not is_mate_after:
            if is_best_move:
                classification = Classification.BEST
            else:
                # Apply centipawn-based classification using dynamic thresholds
                for classif in [Classification.BEST, Classification.EXCELLENT, 
                              Classification.GOOD, Classification.INACCURACY,
                              Classification.MISTAKE, Classification.BLUNDER]:
                    threshold = get_evaluation_loss_threshold(classif, eval_before)
                    if eval_loss <= threshold:
                        classification = classif
                        break
                
                if classification is None:
                    classification = Classification.BLUNDER
        
        # No mate before but blundered into mate
        elif not is_mate_before and is_mate_after:
            if is_best_move:
                classification = Classification.BEST
            elif mate_in_after and mate_in_after > 0:
                # Mover is getting mated but found mate for themselves?
                classification = Classification.BEST
            elif mate_in_after and mate_in_after >= -2:
                # Getting mated in 2 or less
                classification = Classification.BLUNDER
            elif mate_in_after and mate_in_after >= -5:
                classification = Classification.MISTAKE
            else:
                classification = Classification.INACCURACY
        
        # Had mate before but lost it
        elif is_mate_before and not is_mate_after:
            if is_best_move:
                classification = Classification.BEST
            elif mate_in_before and mate_in_before < 0:
                # Was getting mated, escaped - this is good
                if eval_after >= 0:
                    classification = Classification.BEST
                else:
                    classification = Classification.GOOD
            elif eval_after >= 400:
                # Still very winning
                classification = Classification.GOOD
            elif eval_after >= 150:
                classification = Classification.INACCURACY
            elif eval_after >= -100:
                classification = Classification.MISTAKE
            else:
                classification = Classification.BLUNDER
        
        # Mate before and after
        elif is_mate_before and is_mate_after:
            if is_best_move:
                classification = Classification.BEST
            elif mate_in_before and mate_in_before > 0:
                # Had mate, what happened?
                if mate_in_after and mate_in_after <= -4:
                    classification = Classification.MISTAKE
                elif mate_in_after and mate_in_after < 0:
                    classification = Classification.BLUNDER
                elif mate_in_after and mate_in_after <= mate_in_before:
                    classification = Classification.BEST
                elif mate_in_after and mate_in_after <= mate_in_before + 2:
                    classification = Classification.EXCELLENT
                else:
                    classification = Classification.GOOD
            else:
                # Was getting mated
                if mate_in_after == mate_in_before:
                    classification = Classification.BEST
                else:
                    classification = Classification.GOOD
        
        # Fallback
        if classification is None:
            if is_best_move:
                classification = Classification.BEST
            else:
                classification = Classification.GOOD
        
        # === BRILLIANT MOVE DETECTION ===
        # A move is brilliant if:
        # 1. It's the best move
        # 2. Player is not already winning easily (second-best eval < 700cp)
        # 3. A piece is left hanging (sacrifice)
        # 4. The sacrifice leads to a good position
        if classification == Classification.BEST and not is_mate_before:
            # Check if player is NOT already winning anyway
            winning_anyway = (
                second_best_eval is not None and 
                second_best_eval >= 700
            )
            
            if not winning_anyway and eval_after >= -50:  # Position after is at least okay
                if not board_before.is_check():
                    # Parse the move
                    try:
                        to_square = chess.parse_square(move_uci[2:4])
                        from_square = chess.parse_square(move_uci[0:2])
                        moved_piece = board_before.piece_at(from_square)
                        
                        # Look for pieces that are now hanging after our move
                        mover_color = board_before.turn
                        
                        for square in chess.SQUARES:
                            piece = board_after.piece_at(square)
                            if not piece:
                                continue
                            if piece.color != mover_color:
                                continue
                            if piece.piece_type in [chess.KING, chess.PAWN]:
                                continue
                            
                            # Skip if this is a recapture situation
                            captured = board_before.piece_at(to_square)
                            if captured and square == to_square:
                                if PIECE_VALUES.get(captured.piece_type, 0) >= PIECE_VALUES.get(piece.piece_type, 0):
                                    continue
                            
                            # Check if this piece is now hanging
                            if is_piece_hanging(fen_before, fen_after, square):
                                classification = Classification.BRILLIANT
                                break
                    except Exception:
                        pass
        
        # === GREAT MOVE DETECTION ===
        # A move is great if:
        # 1. It's the best move (but not brilliant)
        # 2. There's a significant gap (150+ cp) between best and second-best move
        # 3. The moved piece is not left hanging
        if classification == Classification.BEST and not is_mate_before and not is_mate_after:
            if second_best_eval is not None:
                # Gap between best move (eval_before) and second-best move
                eval_gap = eval_before - second_best_eval
                
                if eval_gap >= 150:
                    # Verify moved piece is not hanging
                    try:
                        to_square = chess.parse_square(move_uci[2:4])
                        if not is_piece_hanging(fen_before, fen_after, to_square):
                            classification = Classification.GREAT
                    except Exception:
                        # If we can't parse, still upgrade to great
                        classification = Classification.GREAT
        
        # === SAFETY CHECKS ===
        
        # Don't call it a blunder if still completely winning
        if classification == Classification.BLUNDER:
            if eval_after >= 600:
                classification = Classification.INACCURACY
        
        # Don't call it a blunder if already completely lost
        if classification == Classification.BLUNDER:
            if eval_before <= -600 and not is_mate_before and not is_mate_after:
                classification = Classification.INACCURACY
        
        # Downgrade inaccuracy to good if position is still very winning
        if classification == Classification.INACCURACY:
            if eval_after >= 500:
                classification = Classification.GOOD
        
        return classification
        
    except Exception as e:
        print(f"Error classifying move: {e}")
        import traceback
        traceback.print_exc()
        return Classification.GOOD  # Default to GOOD not BOOK to avoid false positives


def calculate_accuracy(classifications: List[str]) -> float:
    """
    Calculate accuracy percentage from move classifications.
    
    Uses WintrCat's weighted accuracy formula where each classification
    has a value from 0-1 and accuracy is the average.
    
    Args:
        classifications: List of classification strings
    
    Returns:
        Accuracy percentage (0-100)
    """
    if not classifications:
        return 0.0
    
    total_value = sum(
        CLASSIFICATION_VALUES.get(c.lower(), 0.5) 
        for c in classifications
    )
    
    return (total_value / len(classifications)) * 100


def calculate_accuracy_by_color(
    moves: List[Dict],
) -> Dict[str, float]:
    """
    Calculate accuracy for white and black separately.
    
    Args:
        moves: List of move dictionaries with 'color' and 'quality' keys
    
    Returns:
        Dict with 'white' and 'black' accuracy percentages
    """
    white_moves = [m for m in moves if m.get("color") == "w"]
    black_moves = [m for m in moves if m.get("color") == "b"]
    
    white_accuracy = calculate_accuracy([m.get("quality", "good") for m in white_moves])
    black_accuracy = calculate_accuracy([m.get("quality", "good") for m in black_moves])
    
    return {
        "white": round(white_accuracy, 1),
        "black": round(black_accuracy, 1),
    }
