import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { BarChart3, Target, TrendingDown, TrendingUp, AlertTriangle, Award } from 'lucide-react';
import type { UserAnalytics as UserAnalyticsType } from '@/lib/api';

interface UserAnalyticsProps {
  analytics: UserAnalyticsType;
}

export function UserAnalytics({ analytics }: UserAnalyticsProps) {
  if (!analytics || analytics.total_games === 0) {
    return (
      <Card className="glass-card">
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">No analyzed games yet. Analyze some games to see your stats!</p>
        </CardContent>
      </Card>
    );
  }

  const stats = analytics.overall_statistics;
  const weaknesses = analytics.weakness_patterns;
  const recommendations = analytics.recommendations;

  return (
    <div className="space-y-4">
      {/* Overall Statistics */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            Overall Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Total Games</p>
              <p className="text-2xl font-bold">{analytics.total_games}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Moves Analyzed</p>
              <p className="text-2xl font-bold">{analytics.total_moves_analyzed}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Blunders</p>
              <p className="text-2xl font-bold text-red-500">{stats.blunders}</p>
              <p className="text-xs text-muted-foreground">{stats.blunder_rate_percent.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Blunders/Game</p>
              <p className="text-2xl font-bold">{stats.blunders_per_game.toFixed(1)}</p>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Blunder Rate</span>
              <span className="font-medium">{stats.blunder_rate_percent.toFixed(2)}%</span>
            </div>
            <Progress value={stats.blunder_rate_percent} className="h-2" />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Mistake Rate</span>
              <span className="font-medium">{stats.mistake_rate_percent.toFixed(2)}%</span>
            </div>
            <Progress value={stats.mistake_rate_percent} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Weakness Patterns */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Weakness Patterns
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Weakest Game Phase</p>
            <Badge variant="outline" className="text-base px-3 py-1">
              {weaknesses.weakest_game_phase || "N/A"}
            </Badge>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm">Opening</span>
                <span className="text-sm font-medium">
                  {weaknesses.game_phase_breakdown.opening.blunders} blunders ({weaknesses.game_phase_breakdown.opening.percentage.toFixed(1)}%)
                </span>
              </div>
              <Progress value={weaknesses.game_phase_breakdown.opening.percentage} className="h-2" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm">Middlegame</span>
                <span className="text-sm font-medium">
                  {weaknesses.game_phase_breakdown.middlegame.blunders} blunders ({weaknesses.game_phase_breakdown.middlegame.percentage.toFixed(1)}%)
                </span>
              </div>
              <Progress value={weaknesses.game_phase_breakdown.middlegame.percentage} className="h-2" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm">Endgame</span>
                <span className="text-sm font-medium">
                  {weaknesses.game_phase_breakdown.endgame.blunders} blunders ({weaknesses.game_phase_breakdown.endgame.percentage.toFixed(1)}%)
                </span>
              </div>
              <Progress value={weaknesses.game_phase_breakdown.endgame.percentage} className="h-2" />
            </div>
          </div>

          {weaknesses.most_blunder_prone_move && (
            <div className="pt-2 border-t">
              <p className="text-sm text-muted-foreground">
                Most blunder-prone move: <span className="font-medium">Move {weaknesses.most_blunder_prone_move}</span> ({weaknesses.blunders_at_move} blunders)
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card className="glass-card border-primary/20">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            Personalized Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Focus Area</p>
            <Badge variant="default" className="text-base px-3 py-1">
              {recommendations.focus_area}
            </Badge>
          </div>

          <div>
            <p className="text-sm font-medium mb-2">Targeted Practice Themes</p>
            <div className="flex flex-wrap gap-2">
              {recommendations.targeted_themes.map((theme) => (
                <Badge key={theme} variant="secondary">
                  {theme}
                </Badge>
              ))}
            </div>
          </div>

          <div className="p-3 bg-primary/10 rounded-lg border border-primary/20">
            <p className="text-sm font-medium mb-1">Improvement Priority</p>
            <p className="text-sm text-muted-foreground">{recommendations.improvement_priority}</p>
          </div>
        </CardContent>
      </Card>

      {/* Performance Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Color Performance */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-base">Color Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm font-medium mb-2">White</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Wins:</span>
                  <span className="font-medium text-green-500">{analytics.color_performance.white.wins}</span>
                </div>
                <div className="flex justify-between">
                  <span>Losses:</span>
                  <span className="font-medium text-red-500">{analytics.color_performance.white.losses}</span>
                </div>
                <div className="flex justify-between">
                  <span>Draws:</span>
                  <span className="font-medium">{analytics.color_performance.white.draws}</span>
                </div>
              </div>
            </div>
            <div className="pt-2 border-t">
              <p className="text-sm font-medium mb-2">Black</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Wins:</span>
                  <span className="font-medium text-green-500">{analytics.color_performance.black.wins}</span>
                </div>
                <div className="flex justify-between">
                  <span>Losses:</span>
                  <span className="font-medium text-red-500">{analytics.color_performance.black.losses}</span>
                </div>
                <div className="flex justify-between">
                  <span>Draws:</span>
                  <span className="font-medium">{analytics.color_performance.black.draws}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Opening Performance Summary */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-base">Opening Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(analytics.opening_performance).slice(0, 5).map(([opening, stats]: [string, any]) => (
                <div key={opening} className="flex items-center justify-between text-sm pb-2 border-b last:border-0">
                  <span className="font-medium">{opening}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{stats.games} games</span>
                    <Badge variant={stats.wins > stats.losses ? "default" : "secondary"} className="text-xs">
                      {stats.wins}W-{stats.losses}L
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
