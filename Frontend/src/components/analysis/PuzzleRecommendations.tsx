import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Puzzle, Target, ArrowRight, Star } from 'lucide-react';
import type { Puzzle as PuzzleType } from '@/types/chess';

interface PuzzleRecommendationsProps {
  puzzles: PuzzleType[];
  onPuzzleSelect: (puzzle: PuzzleType) => void;
}

const themeColors: Record<string, string> = {
  tactics: 'bg-chart-1/20 text-chart-1 border-chart-1/30',
  forks: 'bg-chart-2/20 text-chart-2 border-chart-2/30',
  pins: 'bg-chart-3/20 text-chart-3 border-chart-3/30',
  endgame: 'bg-chart-4/20 text-chart-4 border-chart-4/30',
  opening: 'bg-chart-5/20 text-chart-5 border-chart-5/30',
  defense: 'bg-primary/20 text-primary border-primary/30',
};

export function PuzzleRecommendations({ puzzles, onPuzzleSelect }: PuzzleRecommendationsProps) {
  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Puzzle className="w-5 h-5 text-primary" />
            Recommended Puzzles
          </CardTitle>
          <Button variant="ghost" size="sm" className="text-xs">
            View all <ArrowRight className="w-3 h-3 ml-1" />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Based on your weaknesses in this game
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {puzzles.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Puzzle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-xs">No puzzles available yet. Analyze a game first!</p>
          </div>
        ) : (
          puzzles.map((puzzle, index) => (
            <Button
              key={puzzle.id || index}
              variant="ghost"
              className="w-full h-auto p-4 justify-start hover:bg-secondary/50 animate-fade-in border border-border/50 cursor-pointer"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onPuzzleSelect(puzzle);
              }}
              style={{ animationDelay: `${index * 100}ms` }}
            >
            <div className="flex items-start gap-4 w-full">
              {/* Mini preview placeholder */}
              <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-chess-light to-chess-dark flex items-center justify-center flex-shrink-0">
                <Target className="w-6 h-6 text-primary" />
              </div>
              
              <div className="flex-1 text-left">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-sm">Puzzle #{puzzle.id}</span>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Star className="w-3 h-3 fill-primary text-primary" />
                    {puzzle.rating}
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-1 mb-2">
                  {puzzle.themes.slice(0, 3).map(theme => (
                    <Badge 
                      key={theme} 
                      variant="outline" 
                      className={`text-[10px] px-1.5 py-0 ${themeColors[theme.toLowerCase()] || 'bg-secondary'}`}
                    >
                      {theme}
                    </Badge>
                  ))}
                </div>
                
                <p className="text-xs text-muted-foreground line-clamp-1">
                  {puzzle.reason}
                </p>
              </div>
            </div>
          </Button>
          ))
        )}
      </CardContent>
    </Card>
  );
}
