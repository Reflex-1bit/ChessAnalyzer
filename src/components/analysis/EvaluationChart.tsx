import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingUp } from 'lucide-react';

interface EvaluationPoint {
  move: number;
  evaluation: number;
  quality?: string;
}

interface EvaluationChartProps {
  data: EvaluationPoint[];
  currentMove: number;
  onMoveClick: (move: number) => void;
}

export function EvaluationChart({ data, currentMove, onMoveClick }: EvaluationChartProps) {
  // Normalize data for display (cap at +/- 5 for better visualization)
  const normalizedData = data.map(d => ({
    ...d,
    displayEval: Math.max(-5, Math.min(5, d.evaluation)),
  }));

  return (
    <Card className="glass-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary" />
          Game Evaluation
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={normalizedData} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
              <defs>
                <linearGradient id="evalGradientPositive" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--eval-white))" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="hsl(var(--eval-white))" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="evalGradientNegative" x1="0" y1="1" x2="0" y2="0">
                  <stop offset="0%" stopColor="hsl(var(--eval-black))" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="hsl(var(--eval-black))" stopOpacity={0} />
                </linearGradient>
              </defs>
              
              <XAxis 
                dataKey="move" 
                tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                axisLine={{ stroke: 'hsl(var(--border))' }}
                tickLine={false}
              />
              <YAxis 
                domain={[-5, 5]}
                tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                axisLine={false}
                tickLine={false}
                ticks={[-5, -2.5, 0, 2.5, 5]}
              />
              
              <ReferenceLine y={0} stroke="hsl(var(--border))" strokeDasharray="3 3" />
              <ReferenceLine 
                x={currentMove} 
                stroke="hsl(var(--primary))" 
                strokeWidth={2}
              />
              
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
                formatter={(value: number) => [
                  value >= 0 ? `+${value.toFixed(2)}` : value.toFixed(2),
                  'Evaluation'
                ]}
                labelFormatter={(label) => `Move ${label}`}
              />
              
              <Area
                type="monotone"
                dataKey="displayEval"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                fill="url(#evalGradientPositive)"
                activeDot={{ 
                  r: 4, 
                  fill: 'hsl(var(--primary))',
                  stroke: 'hsl(var(--background))',
                  strokeWidth: 2
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        <div className="flex justify-between text-xs text-muted-foreground mt-2 px-2">
          <span>Black winning ↓</span>
          <span>White winning ↑</span>
        </div>
      </CardContent>
    </Card>
  );
}
