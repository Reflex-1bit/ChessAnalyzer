import { useState, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Puzzle, 
  CheckCircle2, 
  XCircle, 
  RotateCcw, 
  Eye, 
  EyeOff,
  ChevronRight,
  Star,
  ExternalLink,
  Lightbulb,
  Trophy,
  Target
} from 'lucide-react';
import type { PlayablePuzzle, PieceType } from '@/types/chess';

// Chess piece SVG URLs (cburnett style - similar to Lichess)
const PIECE_IMAGES: Record<string, string> = {
  'K': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wk.png',
  'Q': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wq.png',
  'R': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wr.png',
  'B': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wb.png',
  'N': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wn.png',
  'P': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wp.png',
  'k': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bk.png',
  'q': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bq.png',
  'r': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/br.png',
  'b': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bb.png',
  'n': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bn.png',
  'p': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bp.png',
};

interface PuzzlePlayerProps {
  puzzle: PlayablePuzzle;
  onComplete?: (success: boolean, attempts: number) => void;
  onClose?: () => void;
}

type PuzzleState = 'playing' | 'correct' | 'incorrect' | 'solved' | 'showing_solution';

function parseFEN(fen: string): (PieceType)[][] {
  // Only parse the board part of the FEN
  const boardPart = fen.split(' ')[0];
  const rows = boardPart.split('/');
  const board: (PieceType)[][] = [];
  
  for (const row of rows) {
    const boardRow: (PieceType)[] = [];
    for (const char of row) {
      if (/\d/.test(char)) {
        for (let i = 0; i < parseInt(char); i++) {
          boardRow.push(null);
        }
      } else {
        boardRow.push(char as PieceType);
      }
    }
    board.push(boardRow);
  }
  
  return board;
}

function getTurnFromFEN(fen: string): 'w' | 'b' {
  const parts = fen.split(' ');
  return (parts[1] || 'w') as 'w' | 'b';
}

function coordsToSquare(rank: number, file: number): string {
  return String.fromCharCode(97 + file) + (8 - rank);
}

function squareToCoords(square: string): { rank: number; file: number } {
  const file = square.charCodeAt(0) - 97;
  const rank = 8 - parseInt(square[1]);
  return { rank, file };
}

// Simple move application (UCI format: e2e4)
function applyMove(fen: string, uciMove: string): string {
  const originalBoard = parseFEN(fen);
  const board = originalBoard.map(row => [...row]); // Deep copy
  const from = uciMove.substring(0, 2);
  const to = uciMove.substring(2, 4);
  const promotion = uciMove.length > 4 ? uciMove[4] : null;
  
  const fromCoords = squareToCoords(from);
  const toCoords = squareToCoords(to);
  
  let piece = board[fromCoords.rank][fromCoords.file];
  const capturedPiece = board[toCoords.rank][toCoords.file];
  
  if (!piece) {
    console.warn(`No piece at ${from} to move`);
    return fen; // Return unchanged if no piece
  }
  
  // Handle promotion
  if (promotion) {
    const isWhite = piece === piece.toUpperCase();
    piece = (isWhite ? promotion.toUpperCase() : promotion.toLowerCase()) as PieceType;
  }
  
  // Move piece
  board[toCoords.rank][toCoords.file] = piece;
  board[fromCoords.rank][fromCoords.file] = null;
  
  // Handle castling
  if (piece === 'K' && from === 'e1') {
    if (to === 'g1') {
      board[7][5] = 'R';
      board[7][7] = null;
    } else if (to === 'c1') {
      board[7][3] = 'R';
      board[7][0] = null;
    }
  } else if (piece === 'k' && from === 'e8') {
    if (to === 'g8') {
      board[0][5] = 'r';
      board[0][7] = null;
    } else if (to === 'c8') {
      board[0][3] = 'r';
      board[0][0] = null;
    }
  }
  
  // Handle en passant - pawn moves diagonally to empty square
  if ((piece === 'P' || piece === 'p') && from[0] !== to[0] && !capturedPiece) {
    // En passant capture - remove the captured pawn
    // For white pawn capturing, the captured pawn is one rank below the destination
    // For black pawn capturing, the captured pawn is one rank above the destination
    if (piece === 'P') {
      board[toCoords.rank + 1][toCoords.file] = null;
    } else {
      board[toCoords.rank - 1][toCoords.file] = null;
    }
  }
  
  // Reconstruct FEN (simplified - just board position)
  const parts = fen.split(' ');
  let newBoardFen = '';
  for (let r = 0; r < 8; r++) {
    let emptyCount = 0;
    for (let f = 0; f < 8; f++) {
      const p = board[r][f];
      if (p === null) {
        emptyCount++;
      } else {
        if (emptyCount > 0) {
          newBoardFen += emptyCount;
          emptyCount = 0;
        }
        newBoardFen += p;
      }
    }
    if (emptyCount > 0) newBoardFen += emptyCount;
    if (r < 7) newBoardFen += '/';
  }
  
  // Toggle turn
  const newTurn = parts[1] === 'w' ? 'b' : 'w';
  
  // Return simplified FEN (board, turn, castling placeholder, en passant, halfmove, fullmove)
  return `${newBoardFen} ${newTurn} ${parts[2] || '-'} ${parts[3] || '-'} ${parts[4] || '0'} ${parts[5] || '1'}`;
}

export function PuzzlePlayer({ puzzle, onComplete, onClose }: PuzzlePlayerProps) {
  const [currentFen, setCurrentFen] = useState(puzzle.fen);
  const [puzzleState, setPuzzleState] = useState<PuzzleState>('playing');
  const [selectedSquare, setSelectedSquare] = useState<string | null>(null);
  const [lastMove, setLastMove] = useState<{ from: string; to: string } | null>(null);
  const [currentMoveIndex, setCurrentMoveIndex] = useState(0);
  const [attempts, setAttempts] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [showingSolution, setShowingSolution] = useState(false);
  const [message, setMessage] = useState<string>('');
  
  // Determine player color (opposite of who moves first in the puzzle)
  const playerTurn = getTurnFromFEN(puzzle.fen);
  const flipped = playerTurn === 'b';
  
  const board = parseFEN(currentFen);
  const solution = puzzle.solution || [];
  const isPlayerTurn = getTurnFromFEN(currentFen) === playerTurn;
  
  // Reset puzzle
  const resetPuzzle = useCallback(() => {
    setCurrentFen(puzzle.fen);
    setPuzzleState('playing');
    setSelectedSquare(null);
    setLastMove(null);
    setCurrentMoveIndex(0);
    setAttempts(0);
    setShowHint(false);
    setShowingSolution(false);
    setMessage('');
  }, [puzzle.fen]);
  
  // Make opponent's response automatically
  useEffect(() => {
    if (puzzleState === 'playing' && !isPlayerTurn && currentMoveIndex < solution.length) {
      // Computer makes its move after a short delay
      const timer = setTimeout(() => {
        const computerMove = solution[currentMoveIndex];
        if (computerMove) {
          const newFen = applyMove(currentFen, computerMove);
          setCurrentFen(newFen);
          setLastMove({
            from: computerMove.substring(0, 2),
            to: computerMove.substring(2, 4),
          });
          setCurrentMoveIndex(prev => prev + 1);
        }
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [currentFen, currentMoveIndex, isPlayerTurn, puzzleState, solution]);
  
  // Check for puzzle completion
  useEffect(() => {
    if (currentMoveIndex >= solution.length && puzzleState === 'playing') {
      setPuzzleState('solved');
      setMessage('🎉 Puzzle Solved!');
      onComplete?.(true, attempts);
    }
  }, [currentMoveIndex, solution.length, puzzleState, attempts, onComplete]);
  
  const handleSquareClick = (square: string) => {
    if (puzzleState !== 'playing' || !isPlayerTurn) return;
    
    const coords = squareToCoords(square);
    const piece = board[coords.rank]?.[coords.file];
    
    if (selectedSquare) {
      // Trying to make a move
      if (selectedSquare === square) {
        // Deselect
        setSelectedSquare(null);
        return;
      }
      
      // Construct move in UCI format
      const attemptedMove = selectedSquare + square;
      const expectedMove = solution[currentMoveIndex];
      
      // Check if move is correct (with or without promotion)
      const isCorrect = expectedMove && (
        attemptedMove === expectedMove ||
        attemptedMove === expectedMove.substring(0, 4) // Allow move without promotion specification
      );
      
      if (isCorrect) {
        // Correct move!
        const moveToApply = expectedMove; // Use full expected move (with promotion)
        const newFen = applyMove(currentFen, moveToApply);
        setCurrentFen(newFen);
        setLastMove({ from: selectedSquare, to: square });
        setSelectedSquare(null);
        setCurrentMoveIndex(prev => prev + 1);
        setPuzzleState('correct');
        setMessage('✓ Correct!');
        
        // Reset to playing after brief feedback
        setTimeout(() => {
          if (currentMoveIndex + 1 < solution.length) {
            setPuzzleState('playing');
            setMessage('');
          }
        }, 300);
      } else {
        // Wrong move
        setAttempts(prev => prev + 1);
        setPuzzleState('incorrect');
        setMessage('✗ Not quite. Try again!');
        setSelectedSquare(null);
        
        // Reset to playing after brief feedback
        setTimeout(() => {
          setPuzzleState('playing');
          setMessage('');
        }, 1000);
      }
    } else {
      // Selecting a piece
      const isWhitePiece = piece && piece === piece.toUpperCase();
      const shouldSelect = playerTurn === 'w' ? isWhitePiece : !isWhitePiece && piece;
      
      if (shouldSelect) {
        setSelectedSquare(square);
      }
    }
  };
  
  const showFullSolution = () => {
    setShowingSolution(true);
    setPuzzleState('showing_solution');
    
    // Replay solution from beginning
    let fen = puzzle.fen;
    let moveIdx = 0;
    
    const playNextMove = () => {
      if (moveIdx < solution.length) {
        const move = solution[moveIdx];
        fen = applyMove(fen, move);
        setCurrentFen(fen);
        setLastMove({
          from: move.substring(0, 2),
          to: move.substring(2, 4),
        });
        moveIdx++;
        setTimeout(playNextMove, 800);
      }
    };
    
    playNextMove();
  };
  
  const getHintText = () => {
    if (!showHint || currentMoveIndex >= solution.length) return null;
    const nextMove = solution[currentMoveIndex];
    if (!nextMove) return null;
    
    const from = nextMove.substring(0, 2);
    const to = nextMove.substring(2, 4);
    return `Hint: Move from ${from} to ${to}`;
  };
  
  const progress = solution.length > 0 ? (currentMoveIndex / solution.length) * 100 : 0;
  
  const renderSquare = (rank: number, file: number) => {
    const actualRank = flipped ? 7 - rank : rank;
    const actualFile = flipped ? 7 - file : file;
    const square = coordsToSquare(actualRank, actualFile);
    const piece = board[actualRank]?.[actualFile];
    const isLight = (actualRank + actualFile) % 2 === 0;
    const isSelected = selectedSquare === square;
    const isLastMoveSquare = lastMove && (square === lastMove.from || square === lastMove.to);
    
    // Highlight hint square
    const isHintSquare = showHint && currentMoveIndex < solution.length && solution[currentMoveIndex]?.substring(0, 2) === square;
    
    return (
      <div
        key={square}
        onClick={() => handleSquareClick(square)}
        className={cn(
          'relative aspect-square flex items-center justify-center cursor-pointer transition-all duration-150',
          isLight ? 'bg-chess-light' : 'bg-chess-dark',
          isLastMoveSquare && (isLight ? 'bg-[hsl(60,80%,70%)]' : 'bg-[hsl(60,70%,50%)]'),
          isSelected && 'ring-4 ring-primary ring-inset',
          isHintSquare && 'ring-4 ring-yellow-400 ring-inset animate-pulse',
          puzzleState === 'correct' && isLastMoveSquare && 'bg-green-400/50',
          puzzleState === 'incorrect' && 'opacity-90',
          'hover:brightness-110'
        )}
      >
        {/* Coordinate labels */}
        {file === 0 && (
          <span className={cn(
            'absolute top-0.5 left-1 text-[10px] font-semibold select-none',
            isLight ? 'text-chess-dark' : 'text-chess-light'
          )}>
            {8 - actualRank}
          </span>
        )}
        {rank === 7 && (
          <span className={cn(
            'absolute bottom-0.5 right-1 text-[10px] font-semibold select-none',
            isLight ? 'text-chess-dark' : 'text-chess-light'
          )}>
            {String.fromCharCode(97 + actualFile)}
          </span>
        )}
        
        {/* Piece */}
        {piece && (
          <img 
            src={PIECE_IMAGES[piece]}
            alt={piece}
            className={cn(
              'w-[85%] h-[85%] object-contain select-none pointer-events-none transition-transform',
            )}
            draggable={false}
          />
        )}
      </div>
    );
  };

  // If it's a training link (no actual puzzle), show a different UI
  if (puzzle.isTrainingLink || !solution || solution.length === 0) {
    return (
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Puzzle className="w-5 h-5 text-primary" />
            Practice {puzzle.theme || 'Tactics'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center py-8">
            <Target className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
            <p className="text-muted-foreground mb-4">
              Practice {puzzle.theme || 'tactical'} puzzles on Lichess
            </p>
            <Button asChild>
              <a href={puzzle.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="w-4 h-4 mr-2" />
                Open on Lichess
              </a>
            </Button>
          </div>
          {onClose && (
            <Button variant="outline" onClick={onClose} className="w-full">
              Close
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Puzzle className="w-5 h-5 text-primary" />
            Puzzle
            {puzzle.puzzle_id && (
              <span className="text-sm font-normal text-muted-foreground">
                #{puzzle.puzzle_id}
              </span>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <Star className="w-3 h-3 fill-primary text-primary" />
              {puzzle.rating || 1500}
            </Badge>
            {puzzle.url && (
              <Button variant="ghost" size="sm" asChild>
                <a href={puzzle.url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="w-4 h-4" />
                </a>
              </Button>
            )}
          </div>
        </div>
        
        {/* Themes */}
        <div className="flex flex-wrap gap-1 mt-2">
          {(puzzle.themes || [puzzle.theme]).filter(Boolean).map(theme => (
            <Badge key={theme} variant="secondary" className="text-xs">
              {theme}
            </Badge>
          ))}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Turn indicator */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <div className={cn(
              'w-4 h-4 rounded-full border-2',
              playerTurn === 'w' ? 'bg-white border-gray-400' : 'bg-gray-800 border-gray-600'
            )} />
            <span>{playerTurn === 'w' ? 'White' : 'Black'} to play</span>
          </div>
          <span className="text-xs text-muted-foreground">
            {currentMoveIndex}/{solution.length} moves
          </span>
        </div>
        
        {/* Progress bar */}
        <Progress value={progress} className="h-2" />
        
        {/* Message */}
        {message && (
          <div className={cn(
            'text-center py-2 px-4 rounded-lg text-sm font-medium',
            puzzleState === 'correct' && 'bg-green-500/20 text-green-400',
            puzzleState === 'incorrect' && 'bg-red-500/20 text-red-400',
            puzzleState === 'solved' && 'bg-primary/20 text-primary',
          )}>
            {message}
          </div>
        )}
        
        {/* Hint text */}
        {showHint && getHintText() && (
          <div className="text-center py-2 px-4 rounded-lg bg-yellow-500/20 text-yellow-400 text-sm">
            {getHintText()}
          </div>
        )}
        
        {/* Chessboard */}
        <div className="flex justify-center">
          <div className="w-80 md:w-96 rounded-lg overflow-hidden shadow-2xl">
            <div className="grid grid-cols-8 aspect-square">
              {Array.from({ length: 64 }).map((_, i) => {
                const rank = Math.floor(i / 8);
                const file = i % 8;
                return renderSquare(rank, file);
              })}
            </div>
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex flex-wrap items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowHint(!showHint)}
            disabled={puzzleState === 'solved' || puzzleState === 'showing_solution'}
          >
            {showHint ? <EyeOff className="w-4 h-4 mr-1" /> : <Lightbulb className="w-4 h-4 mr-1" />}
            {showHint ? 'Hide Hint' : 'Hint'}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={showFullSolution}
            disabled={puzzleState === 'solved' || puzzleState === 'showing_solution'}
          >
            <Eye className="w-4 h-4 mr-1" />
            Show Solution
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={resetPuzzle}
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            Retry
          </Button>
        </div>
        
        {/* Solved state */}
        {puzzleState === 'solved' && (
          <div className="text-center p-4 bg-primary/10 rounded-lg border border-primary/20">
            <Trophy className="w-8 h-8 mx-auto mb-2 text-primary" />
            <p className="font-medium">Puzzle Complete!</p>
            <p className="text-sm text-muted-foreground">
              Solved in {attempts === 0 ? 'first try' : `${attempts + 1} attempts`}
            </p>
            {onClose && (
              <Button className="mt-4" onClick={onClose}>
                <ChevronRight className="w-4 h-4 mr-1" />
                Next Puzzle
              </Button>
            )}
          </div>
        )}
        
        {/* Attempts counter */}
        {attempts > 0 && puzzleState !== 'solved' && (
          <p className="text-xs text-center text-muted-foreground">
            Attempts: {attempts}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
