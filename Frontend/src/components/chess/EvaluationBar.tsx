import { cn } from '@/lib/utils';

interface EvaluationBarProps {
  evaluation: number; // Positive = white winning, negative = black winning
  orientation?: 'vertical' | 'horizontal';
  showValue?: boolean;
  className?: string;
}

export function EvaluationBar({ 
  evaluation, 
  orientation = 'vertical',
  showValue = true,
  className 
}: EvaluationBarProps) {
  // Convert evaluation to percentage (sigmoid-like function)
  // Cap at +/- 10 for display purposes
  const cappedEval = Math.max(-10, Math.min(10, evaluation));
  const whitePercentage = 50 + (cappedEval / 10) * 50;
  
  const formatEval = (val: number) => {
    if (Math.abs(val) > 100) return val > 0 ? '+M' : '-M'; // Mate
    return val >= 0 ? `+${val.toFixed(1)}` : val.toFixed(1);
  };

  if (orientation === 'horizontal') {
    return (
      <div className={cn('relative h-6 w-full rounded-full overflow-hidden bg-eval-black', className)}>
        <div 
          className="absolute inset-y-0 left-0 eval-bar-white transition-all duration-500 ease-out animate-eval-change"
          style={{ width: `${whitePercentage}%` }}
        />
        {showValue && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={cn(
              'text-xs font-mono font-medium',
              evaluation >= 0 ? 'text-eval-black' : 'text-eval-white'
            )}>
              {formatEval(evaluation)}
            </span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={cn('relative w-6 h-full rounded-full overflow-hidden bg-eval-black flex flex-col-reverse', className)}>
      <div 
        className="eval-bar-white transition-all duration-500 ease-out animate-eval-change rounded-t-full"
        style={{ height: `${whitePercentage}%` }}
      />
      {showValue && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn(
            'text-[10px] font-mono font-bold writing-mode-vertical rotate-180',
            evaluation >= 0 ? 'text-eval-black' : 'text-eval-white'
          )}
          style={{ writingMode: 'vertical-rl' }}
          >
            {formatEval(evaluation)}
          </span>
        </div>
      )}
    </div>
  );
}
