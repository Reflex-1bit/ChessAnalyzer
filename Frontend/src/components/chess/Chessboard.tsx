import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import type { PieceType, MoveQuality } from '@/types/chess';

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

interface ChessboardProps {
  position?: string;
  lastMove?: { from: string; to: string };
  highlightedSquares?: { square: string; color: MoveQuality }[];
  onSquareClick?: (square: string) => void;
  flipped?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const initialPosition = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR';

function parseFEN(fen: string): (PieceType)[][] {
  const rows = fen.split('/');
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

function coordsToSquare(rank: number, file: number): string {
  return String.fromCharCode(97 + file) + (8 - rank);
}

export function Chessboard({ 
  position = initialPosition, 
  lastMove,
  highlightedSquares = [],
  onSquareClick,
  flipped = false,
  size = 'md'
}: ChessboardProps) {
  const [animatingPiece, setAnimatingPiece] = useState<string | null>(null);
  const board = parseFEN(position);
  
  const sizeClasses = {
    sm: 'w-64',
    md: 'w-80 md:w-96',
    lg: 'w-96 md:w-[480px]',
  };

  const getSquareHighlight = (square: string) => {
    const highlight = highlightedSquares.find(h => h.square === square);
    if (highlight) {
      // WintrCat classification colors
      const colorMap: Record<MoveQuality, string> = {
        brilliant: 'ring-2 ring-move-brilliant ring-inset',
        great: 'ring-2 ring-move-great ring-inset',
        best: 'ring-2 ring-move-best ring-inset',
        excellent: 'ring-2 ring-move-excellent ring-inset',
        good: 'ring-2 ring-move-good ring-inset',
        book: 'ring-2 ring-move-book ring-inset',
        forced: 'ring-2 ring-move-forced ring-inset',
        inaccuracy: 'ring-2 ring-move-inaccuracy ring-inset',
        mistake: 'ring-2 ring-move-mistake ring-inset',
        blunder: 'ring-2 ring-move-blunder ring-inset',
        neutral: '',
      };
      return colorMap[highlight.color];
    }
    return '';
  };

  const isLastMoveSquare = (square: string) => {
    if (!lastMove) return false;
    return square === lastMove.from || square === lastMove.to;
  };

  useEffect(() => {
    if (lastMove) {
      setAnimatingPiece(lastMove.to);
      const timer = setTimeout(() => setAnimatingPiece(null), 300);
      return () => clearTimeout(timer);
    }
  }, [lastMove]);

  const renderSquare = (rank: number, file: number) => {
    const actualRank = flipped ? 7 - rank : rank;
    const actualFile = flipped ? 7 - file : file;
    const square = coordsToSquare(actualRank, actualFile);
    const piece = board[actualRank]?.[actualFile];
    const isLight = (actualRank + actualFile) % 2 === 0;
    const isAnimating = animatingPiece === square;

    return (
      <div
        key={square}
        onClick={() => onSquareClick?.(square)}
        className={cn(
          'relative aspect-square flex items-center justify-center cursor-pointer transition-all duration-150',
          isLight ? 'bg-chess-light' : 'bg-chess-dark',
          isLastMoveSquare(square) && (isLight ? 'bg-[hsl(60,80%,70%)]' : 'bg-[hsl(60,70%,50%)]'),
          getSquareHighlight(square),
          onSquareClick && 'hover:brightness-110'
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
              isAnimating && 'animate-piece-move'
            )}
            draggable={false}
          />
        )}
      </div>
    );
  };

  return (
    <div className={cn('rounded-lg overflow-hidden shadow-2xl glow-primary', sizeClasses[size])}>
      <div className="grid grid-cols-8 aspect-square">
        {Array.from({ length: 64 }).map((_, i) => {
          const rank = Math.floor(i / 8);
          const file = i % 8;
          return renderSquare(rank, file);
        })}
      </div>
    </div>
  );
}
