import { cn } from '@/lib/utils';
import type { ChessMove, MoveQuality } from '@/types/chess';
import { Zap, Star, AlertTriangle, AlertCircle, BookOpen, Sparkles, CheckCircle2, Trophy, Lock } from 'lucide-react';

interface MoveListProps {
  moves: ChessMove[];
  currentMoveIndex: number;
  onMoveClick: (index: number) => void;
}

// WintrCat classification icons
const qualityIcons: Record<MoveQuality, React.ReactNode> = {
  brilliant: <Sparkles className="w-3 h-3 text-move-brilliant" />,
  great: <Trophy className="w-3 h-3 text-move-great" />,
  best: <CheckCircle2 className="w-3 h-3 text-move-best" />,
  excellent: <Zap className="w-3 h-3 text-move-excellent" />,
  good: <Star className="w-3 h-3 text-move-good" />,
  book: <BookOpen className="w-3 h-3 text-move-book" />,
  forced: <Lock className="w-3 h-3 text-move-forced" />,
  inaccuracy: <AlertTriangle className="w-3 h-3 text-move-inaccuracy" />,
  mistake: <AlertCircle className="w-3 h-3 text-move-mistake" />,
  blunder: <AlertCircle className="w-3 h-3 text-move-blunder" />,
  neutral: null,
};

// WintrCat classification colors
const qualityColors: Record<MoveQuality, string> = {
  brilliant: 'bg-move-brilliant/10 border-move-brilliant/30 text-move-brilliant',
  great: 'bg-move-great/10 border-move-great/30 text-move-great',
  best: 'bg-move-best/10 border-move-best/30 text-move-best',
  excellent: 'bg-move-excellent/10 border-move-excellent/30 text-move-excellent',
  good: 'bg-move-good/10 border-move-good/30 text-move-good',
  book: 'bg-move-book/10 border-move-book/30 text-move-book',
  forced: 'bg-move-forced/10 border-move-forced/30 text-move-forced',
  inaccuracy: 'bg-move-inaccuracy/10 border-move-inaccuracy/30 text-move-inaccuracy',
  mistake: 'bg-move-mistake/10 border-move-mistake/30 text-move-mistake',
  blunder: 'bg-move-blunder/10 border-move-blunder/30 text-move-blunder',
  neutral: 'hover:bg-secondary/50',
};

export function MoveList({ moves, currentMoveIndex, onMoveClick }: MoveListProps) {
  // Group moves into pairs (white + black)
  const movePairs: { moveNumber: number; white?: ChessMove; black?: ChessMove; whiteIndex: number; blackIndex?: number }[] = [];
  
  for (let i = 0; i < moves.length; i += 2) {
    movePairs.push({
      moveNumber: Math.floor(i / 2) + 1,
      white: moves[i],
      black: moves[i + 1],
      whiteIndex: i,
      blackIndex: i + 1 < moves.length ? i + 1 : undefined,
    });
  }

  return (
    <div className="flex flex-col gap-1 p-3 bg-card rounded-xl border border-border max-h-[400px] overflow-y-auto scrollbar-thin">
      <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
        Moves
      </div>
      {movePairs.map((pair) => (
        <div key={pair.moveNumber} className="flex items-center gap-1 text-sm">
          <span className="w-8 text-muted-foreground font-mono text-xs">
            {pair.moveNumber}.
          </span>
          
          {/* White move */}
          {pair.white && (
            <button
              onClick={() => onMoveClick(pair.whiteIndex)}
              className={cn(
                'flex items-center gap-1 px-2 py-1 rounded-md font-mono text-xs transition-all border border-transparent',
                currentMoveIndex === pair.whiteIndex && 'ring-2 ring-primary ring-offset-1 ring-offset-background',
                pair.white.quality && pair.white.quality !== 'neutral' 
                  ? qualityColors[pair.white.quality]
                  : 'hover:bg-secondary/50'
              )}
            >
              {pair.white.quality && qualityIcons[pair.white.quality]}
              <span>{pair.white.san}</span>
            </button>
          )}
          
          {/* Black move */}
          {pair.black && (
            <button
              onClick={() => onMoveClick(pair.blackIndex!)}
              className={cn(
                'flex items-center gap-1 px-2 py-1 rounded-md font-mono text-xs transition-all border border-transparent',
                currentMoveIndex === pair.blackIndex && 'ring-2 ring-primary ring-offset-1 ring-offset-background',
                pair.black.quality && pair.black.quality !== 'neutral'
                  ? qualityColors[pair.black.quality]
                  : 'hover:bg-secondary/50'
              )}
            >
              {pair.black.quality && qualityIcons[pair.black.quality]}
              <span>{pair.black.san}</span>
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
