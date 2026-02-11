import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Zap, TrendingUp, Sparkles, AlertCircle } from 'lucide-react';
import type { CriticalMoment } from '@/types/chess';

interface CriticalMomentsProps {
  moments: CriticalMoment[];
  onMomentClick: (moveNumber: number) => void;
}

const momentIcons = {
  blunder: AlertTriangle,
  mistake: AlertCircle,
  inaccuracy: TrendingUp,
  missed_win: TrendingUp,
  turning_point: Zap,
  brilliant: Sparkles,
};

const momentColors = {
  blunder: 'text-move-blunder bg-move-blunder/10 border-move-blunder/20',
  mistake: 'text-move-mistake bg-move-mistake/10 border-move-mistake/20',
  inaccuracy: 'text-move-inaccuracy bg-move-inaccuracy/10 border-move-inaccuracy/20',
  missed_win: 'text-move-inaccuracy bg-move-inaccuracy/10 border-move-inaccuracy/20',
  turning_point: 'text-primary bg-primary/10 border-primary/20',
  brilliant: 'text-move-brilliant bg-move-brilliant/10 border-move-brilliant/20',
};

const momentLabels = {
  blunder: 'Blunder',
  mistake: 'Mistake',
  inaccuracy: 'Inaccuracy',
  missed_win: 'Missed Win',
  turning_point: 'Turning Point',
  brilliant: 'Brilliant Move',
};

export function CriticalMoments({ moments, onMomentClick }: CriticalMomentsProps) {
  if (moments.length === 0) {
    return (
      <Card className="glass-card">
        <CardContent className="flex flex-col items-center justify-center py-8 text-center">
          <Zap className="w-10 h-10 text-muted-foreground/50 mb-2" />
          <p className="text-sm text-muted-foreground">No critical moments detected</p>
          <p className="text-xs text-muted-foreground/70">A well-played game!</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary" />
          Critical Moments
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {moments.map((moment, index) => {
          const Icon = momentIcons[moment.type as keyof typeof momentIcons] || AlertTriangle;
          const colorClass = momentColors[moment.type as keyof typeof momentColors] || momentColors.blunder;
          const label = momentLabels[moment.type as keyof typeof momentLabels] || 'Critical Moment';
          
          return (
            <Button
              key={index}
              variant="ghost"
              className={`w-full justify-start h-auto py-3 px-3 border ${colorClass} hover:opacity-80`}
              onClick={() => onMomentClick(moment.moveNumber)}
            >
              <div className="flex items-start gap-3 w-full">
                <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div className="flex-1 text-left">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm">{label}</span>
                    <span className="text-xs opacity-70">Move {moment.moveNumber}</span>
                  </div>
                  {moment.explanation && (
                    <p className="text-xs opacity-80 line-clamp-2">
                      {moment.explanation}
                    </p>
                  )}
                  {moment.playedMove && moment.bestMove && (
                    <div className="flex items-center gap-2 mt-2 text-xs font-mono opacity-70">
                      <span>Played: {moment.playedMove}</span>
                      <span>→</span>
                      <span className="text-move-great">Best: {moment.bestMove}</span>
                    </div>
                  )}
                </div>
              </div>
            </Button>
          );
        })}
      </CardContent>
    </Card>
  );
}
