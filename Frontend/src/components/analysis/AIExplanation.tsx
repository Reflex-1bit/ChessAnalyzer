import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Brain, Lightbulb, ArrowRight, ChevronDown, ChevronUp, GraduationCap, Swords, Target } from 'lucide-react';
import { MoveQualityBadge } from '@/components/chess/MoveQualityBadge';
import type { ChessMove } from '@/types/chess';

interface AIExplanationProps {
  move: ChessMove | null;
  moveNumber: number;
  isPlayerMove: boolean;
}

export function AIExplanation({ move, moveNumber, isPlayerMove }: AIExplanationProps) {
  const [advancedMode, setAdvancedMode] = useState(false);
  const [showAlternatives, setShowAlternatives] = useState(false);

  if (!move) {
    return (
      <Card className="glass-card">
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <Brain className="w-12 h-12 text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground">Select a move to see AI analysis</p>
        </CardContent>
      </Card>
    );
  }

  // Get explanation from backend analysis (if available) or generate fallback
  const moveData = move as any;
  
  // Use real explanations from backend if available
  const hasRealExplanation = moveData.explanation || moveData.explanation_advanced;
  
  const simpleExplanation = moveData.explanation || generateFallbackSimple(move, moveData);
  const advancedExplanation = moveData.explanation_advanced || generateFallbackAdvanced(move, moveData);
  
  // Tactical motifs from analysis
  const tacticalMotifs = moveData.tactical_motifs || [];
  
  // Get evaluation info
  const evalBefore = (moveData.evaluation_before || 0) / 100;
  const evalAfter = (moveData.evaluation_after || 0) / 100;
  const evalLoss = Math.abs(moveData.evaluation_loss || 0) / 100;
  
  const quality = move.quality || 'neutral';

  return (
    <Card className="glass-card animate-slide-in-right">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            AI Analysis
          </CardTitle>
          <div className="flex items-center gap-2 text-sm">
            <GraduationCap className="w-4 h-4 text-muted-foreground" />
            <span className="text-muted-foreground">Advanced</span>
            <Switch checked={advancedMode} onCheckedChange={setAdvancedMode} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Move info */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50">
          <span className="text-sm text-muted-foreground">Move {moveNumber}</span>
          <span className="font-mono text-lg font-semibold">{move.san}</span>
          {move.quality && <MoveQualityBadge quality={move.quality} size="sm" />}
          {isPlayerMove && <Badge variant="outline" className="text-xs">Your move</Badge>}
        </div>

        {/* Explanation */}
        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <Lightbulb className="w-4 h-4 text-primary mt-1 flex-shrink-0" />
            <p className="text-sm leading-relaxed">
              {advancedMode ? advancedExplanation : simpleExplanation}
            </p>
          </div>
        </div>

        {/* Tactical motifs (if any) */}
        {tacticalMotifs.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {tacticalMotifs.map((motif: string, idx: number) => (
              <Badge key={idx} variant="secondary" className="text-xs gap-1">
                <Swords className="w-3 h-3" />
                {formatMotif(motif)}
              </Badge>
            ))}
          </div>
        )}

        {/* Evaluation change (for mistakes/blunders) */}
        {['blunder', 'mistake', 'inaccuracy'].includes(quality) && evalLoss > 0 && (
          <div className="p-2 rounded-lg bg-destructive/10 border border-destructive/20">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Evaluation change:</span>
              <span className="font-mono text-destructive">
                {evalBefore >= 0 ? '+' : ''}{evalBefore.toFixed(1)} → {evalAfter >= 0 ? '+' : ''}{evalAfter.toFixed(1)}
              </span>
            </div>
          </div>
        )}

        {/* Best move suggestion */}
        {move.bestMove && ['blunder', 'mistake', 'inaccuracy'].includes(quality) && (
          <div className="p-3 rounded-lg bg-move-best/10 border border-move-best/20">
            <div className="flex items-center gap-2 text-sm mb-1">
              <Target className="w-4 h-4 text-move-best" />
              <span className="font-medium text-move-best">Better move</span>
            </div>
            <span className="font-mono text-lg">{move.bestMove}</span>
          </div>
        )}

        {/* Alternatives toggle */}
        <Button 
          variant="ghost" 
          size="sm" 
          className="w-full"
          onClick={() => setShowAlternatives(!showAlternatives)}
        >
          {showAlternatives ? <ChevronUp className="w-4 h-4 mr-2" /> : <ChevronDown className="w-4 h-4 mr-2" />}
          {showAlternatives ? 'Hide' : 'Show'} alternative lines
        </Button>

        {showAlternatives && (
          <div className="space-y-2 p-3 rounded-lg bg-secondary/30">
            {move.bestMove && (
              <div className="flex items-center justify-between text-sm">
                <span className="font-mono">1. {move.bestMove}</span>
                <span className="text-move-best font-mono">Best</span>
              </div>
            )}
            <div className="flex items-center justify-between text-sm">
              <span className="font-mono">2. {move.san}</span>
              <span className={`font-mono ${getQualityColor(quality)}`}>
                {quality.charAt(0).toUpperCase() + quality.slice(1)}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Helper to format tactical motif names
function formatMotif(motif: string): string {
  const motifNames: Record<string, string> = {
    'check': 'Check',
    'checkmate': 'Checkmate',
    'fork': 'Fork',
    'pin': 'Pin',
    'sacrifice': 'Sacrifice',
    'king_attack': 'King Attack',
    'winning_exchange': 'Winning Trade',
    'losing_exchange': 'Bad Trade',
    'promotion_to_queen': 'Promotion',
  };
  return motifNames[motif] || motif.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// Helper for quality colors
function getQualityColor(quality: string): string {
  const colors: Record<string, string> = {
    brilliant: 'text-move-brilliant',
    great: 'text-move-great',
    best: 'text-move-best',
    excellent: 'text-move-excellent',
    good: 'text-move-good',
    book: 'text-move-book',
    forced: 'text-move-forced',
    inaccuracy: 'text-move-inaccuracy',
    mistake: 'text-move-mistake',
    blunder: 'text-move-blunder',
  };
  return colors[quality] || 'text-muted-foreground';
}

// Fallback explanation generators (when backend doesn't provide one)
function generateFallbackSimple(move: ChessMove, data: any): string {
  const quality = move.quality || 'neutral';
  const evalLoss = Math.abs(data.evaluation_loss || 0) / 100;
  const bestMove = move.bestMove;
  
  switch (quality) {
    case 'brilliant':
      return `Brilliant! An exceptional move finding a hidden winning idea.`;
    case 'great':
      return `Great move! This is significantly stronger than alternatives.`;
    case 'best':
      return `This is the engine's top choice - the strongest move in the position.`;
    case 'excellent':
      return `Excellent! Very close to the best move in this position.`;
    case 'good':
      return `A solid move that maintains the position.`;
    case 'book':
      return `Standard opening move following established theory.`;
    case 'forced':
      return `This was the only legal move available.`;
    case 'inaccuracy':
      return bestMove 
        ? `Small inaccuracy losing ~${evalLoss.toFixed(1)} pawns. ${bestMove} was more accurate.`
        : `A slight inaccuracy costing about ${evalLoss.toFixed(1)} pawns.`;
    case 'mistake':
      return bestMove
        ? `Mistake losing ~${evalLoss.toFixed(1)} pawns. ${bestMove} was much better.`
        : `A significant mistake losing about ${evalLoss.toFixed(1)} pawns.`;
    case 'blunder':
      return bestMove
        ? `Blunder losing ${evalLoss.toFixed(1)}+ pawns! ${bestMove} was essential.`
        : `Serious blunder losing approximately ${evalLoss.toFixed(1)} pawns.`;
    default:
      return `Move ${move.san} played.`;
  }
}

function generateFallbackAdvanced(move: ChessMove, data: any): string {
  const quality = move.quality || 'neutral';
  const evalLoss = Math.abs(data.evaluation_loss || 0) / 100;
  const evalBefore = (data.evaluation_before || 0) / 100;
  const evalAfter = (data.evaluation_after || 0) / 100;
  const bestMove = move.bestMove;
  
  switch (quality) {
    case 'brilliant':
      return `${move.san} demonstrates deep calculation with a non-obvious winning continuation. Material may be sacrificed for a decisive attack.`;
    case 'great':
      return `${move.san} stands out as clearly the best move, significantly stronger than alternatives. This finds the critical continuation.`;
    case 'best':
      return `${move.san} is the objectively strongest continuation. This move maintains optimal piece activity and limits counterplay.`;
    case 'excellent':
      return `${move.san} is a very strong move, nearly matching the engine's top choice with minimal difference in evaluation.`;
    case 'good':
      return `${move.san} is a reasonable move with no significant drawbacks. The position remains balanced.`;
    case 'book':
      return `This is a well-known theoretical move. Opening preparation helps navigate familiar positions efficiently.`;
    case 'forced':
      return `With only one legal option, ${move.san} was forced. The position left no alternatives.`;
    case 'inaccuracy':
      return `${move.san} gives up approximately ${evalLoss.toFixed(1)} pawns worth of advantage. ${bestMove ? `The engine prefers ${bestMove}.` : ''} Position: ${evalBefore.toFixed(1)} → ${evalAfter.toFixed(1)}`;
    case 'mistake':
      return `${move.san} is a clear mistake, dropping about ${evalLoss.toFixed(1)} pawns. ${bestMove ? `The correct move was ${bestMove}.` : ''} This overlooked a tactical opportunity.`;
    case 'blunder':
      return `${move.san} is a serious error losing approximately ${evalLoss.toFixed(1)} pawns. ${bestMove ? `The saving move was ${bestMove}.` : ''} This type of mistake often decides games.`;
    default:
      return `The move ${move.san} was played in this position.`;
  }
}
