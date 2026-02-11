import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Trophy, Target, AlertTriangle, AlertCircle, Sparkles, Clock, CheckCircle2, Zap } from 'lucide-react';
import type { GameSummary } from '@/types/chess';

interface GameSummaryCardProps {
  game: GameSummary;
  playerColor: 'white' | 'black';
}

export function GameSummaryCard({ game, playerColor }: GameSummaryCardProps) {
  // Safety checks
  if (!game) {
    return <Card><CardContent>No game data</CardContent></Card>;
  }
  
  const accuracy = game.accuracy || { white: 0, black: 0 };
  const playerAccuracy = playerColor === 'white' ? accuracy.white : accuracy.black;
  const opponentAccuracy = playerColor === 'white' ? accuracy.black : accuracy.white;
  
  const whiteName = game.white || game.white_player || 'White';
  const blackName = game.black || game.black_player || 'Black';
  const playerName = playerColor === 'white' ? whiteName : blackName;
  const opponentName = playerColor === 'white' ? blackName : whiteName;
  
  const won = (playerColor === 'white' && game.result === '1-0') || 
              (playerColor === 'black' && game.result === '0-1');
  const drew = game.result === '1/2-1/2';

  // Count move types for player (WintrCat classifications)
  const moveCounts = {
    brilliant: 0,
    great: 0,
    best: 0,
    excellent: 0,
    good: 0,
    inaccuracy: 0,
    mistake: 0,
    blunder: 0,
  };

  const moves = game.moves || [];
  moves.forEach((move) => {
    // Use move.color if available, otherwise fall back to calculating from move_number
    const moveColor = move.color || (move.move_number ? (move.move_number % 2 === 1 ? 'w' : 'b') : null);
    const isPlayerMove = (playerColor === 'white' && moveColor === 'w') || 
                         (playerColor === 'black' && moveColor === 'b');
    if (isPlayerMove && move.quality) {
      if (move.quality in moveCounts) {
        moveCounts[move.quality as keyof typeof moveCounts]++;
      }
    }
  });
  
  // Combine best moves for display (brilliant + great + best)
  const excellentMoves = moveCounts.brilliant + moveCounts.great + moveCounts.best + moveCounts.excellent;

  return (
    <Card className="glass-card animate-fade-in">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Trophy className={won ? 'text-primary' : drew ? 'text-muted-foreground' : 'text-destructive'} />
            Game Summary
          </CardTitle>
          <Badge variant={won ? 'default' : drew ? 'secondary' : 'destructive'}>
            {won ? 'Victory' : drew ? 'Draw' : 'Defeat'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Players */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-eval-white border border-border" />
            <span className={playerColor === 'white' ? 'font-semibold text-primary' : ''}>
              {whiteName}
            </span>
          </div>
          <span className="text-muted-foreground">vs</span>
          <div className="flex items-center gap-2">
            <span className={playerColor === 'black' ? 'font-semibold text-primary' : ''}>
              {blackName}
            </span>
            <div className="w-3 h-3 rounded-full bg-eval-black border border-border" />
          </div>
        </div>

        {/* Opening & Time Control */}
        <div className="flex flex-wrap gap-2 text-xs">
          {game.timeControl && (
            <Badge variant="secondary" className="gap-1">
              <Clock className="w-3 h-3" />
              {game.timeControl}
            </Badge>
          )}
          {game.opening && (
            <Badge variant="outline">{game.opening}</Badge>
          )}
        </div>

        {/* Accuracy */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Your Accuracy</span>
            <span className="font-mono font-semibold text-primary">{playerAccuracy.toFixed(1)}%</span>
          </div>
          <Progress value={playerAccuracy} className="h-2" />
        </div>

        {/* Move Quality Breakdown - WintrCat style */}
        <div className="grid grid-cols-6 gap-1.5 pt-2">
          <div className="text-center p-1.5 rounded-lg bg-move-brilliant/10">
            <Sparkles className="w-3.5 h-3.5 mx-auto text-move-brilliant mb-0.5" />
            <span className="text-base font-bold text-move-brilliant">{moveCounts.brilliant}</span>
            <p className="text-[9px] text-muted-foreground">Brilliant</p>
          </div>
          <div className="text-center p-1.5 rounded-lg bg-move-great/10">
            <Trophy className="w-3.5 h-3.5 mx-auto text-move-great mb-0.5" />
            <span className="text-base font-bold text-move-great">{moveCounts.great}</span>
            <p className="text-[9px] text-muted-foreground">Great</p>
          </div>
          <div className="text-center p-1.5 rounded-lg bg-move-best/10">
            <CheckCircle2 className="w-3.5 h-3.5 mx-auto text-move-best mb-0.5" />
            <span className="text-base font-bold text-move-best">{moveCounts.best}</span>
            <p className="text-[9px] text-muted-foreground">Best</p>
          </div>
          <div className="text-center p-1.5 rounded-lg bg-move-inaccuracy/10">
            <AlertTriangle className="w-3.5 h-3.5 mx-auto text-move-inaccuracy mb-0.5" />
            <span className="text-base font-bold text-move-inaccuracy">{moveCounts.inaccuracy}</span>
            <p className="text-[9px] text-muted-foreground">Inaccuracy</p>
          </div>
          <div className="text-center p-1.5 rounded-lg bg-move-mistake/10">
            <AlertCircle className="w-3.5 h-3.5 mx-auto text-move-mistake mb-0.5" />
            <span className="text-base font-bold text-move-mistake">{moveCounts.mistake}</span>
            <p className="text-[9px] text-muted-foreground">Mistake</p>
          </div>
          <div className="text-center p-1.5 rounded-lg bg-move-blunder/10">
            <AlertCircle className="w-3.5 h-3.5 mx-auto text-move-blunder mb-0.5" />
            <span className="text-base font-bold text-move-blunder">{moveCounts.blunder}</span>
            <p className="text-[9px] text-muted-foreground">Blunder</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
