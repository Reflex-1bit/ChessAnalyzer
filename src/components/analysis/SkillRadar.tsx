import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown } from 'lucide-react';
import type { SkillArea } from '@/types/chess';

interface SkillRadarProps {
  skills: SkillArea[];
  gamesAnalyzed?: number;
}

export function SkillRadar({ skills, gamesAnalyzed }: SkillRadarProps) {
  const maxScore = 100;

  // Get color based on score
  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-400';
    if (score >= 60) return 'text-amber-400';
    return 'text-orange-400';
  };

  // Get progress bar color based on score
  const getBarColor = (score: number) => {
    if (score >= 75) return 'from-emerald-500 to-emerald-400';
    if (score >= 60) return 'from-amber-500 to-amber-400';
    return 'from-orange-500 to-orange-400';
  };

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-bold">Skill Profile</CardTitle>
          {gamesAnalyzed !== undefined && gamesAnalyzed > 0 && (
            <span className="text-xs text-muted-foreground">
              Based on {gamesAnalyzed} game{gamesAnalyzed !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {skills.map((skill, index) => (
          <div 
            key={skill.name} 
            className="space-y-2 animate-fade-in" 
            style={{ animationDelay: `${index * 80}ms` }}
          >
            {/* Skill name, improvement badge, and score */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-base font-semibold text-foreground">{skill.name}</span>
                {skill.improvement !== 0 && (
                  skill.improvement > 0 ? (
                    <Badge 
                      variant="secondary" 
                      className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-xs px-2 py-0.5 font-medium"
                    >
                      <TrendingUp className="w-3 h-3 mr-1" />
                      +{skill.improvement}%
                    </Badge>
                  ) : (
                    <Badge 
                      variant="secondary" 
                      className="bg-red-500/20 text-red-400 border-red-500/30 text-xs px-2 py-0.5 font-medium"
                    >
                      <TrendingDown className="w-3 h-3 mr-1" />
                      {skill.improvement}%
                    </Badge>
                  )
                )}
              </div>
              <span className={`text-lg font-bold font-mono ${getScoreColor(skill.score)}`}>
                {skill.score}
              </span>
            </div>
            
            {/* Progress bar */}
            <div className="relative h-2.5 bg-secondary/50 rounded-full overflow-hidden">
              <div 
                className={`absolute inset-y-0 left-0 bg-gradient-to-r ${getBarColor(skill.score)} rounded-full transition-all duration-700 ease-out`}
                style={{ width: `${(skill.score / maxScore) * 100}%` }}
              />
            </div>
            
            {/* Description */}
            <p className="text-sm text-muted-foreground leading-relaxed">{skill.description}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
